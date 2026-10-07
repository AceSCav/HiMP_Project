"""Office-owned Drive documents; credentials and file contents stay server-side."""
import json
from hashlib import sha256
import secrets
from io import BytesIO

import httplib2
from cryptography.fernet import Fernet
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.shortcuts import redirect
from django.utils import timezone
from django.views.decorators.http import require_POST
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_httplib2 import AuthorizedHttp
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload

from .models import Cliente, DocumentoCliente, DriveConnection

SCOPES = ['https://www.googleapis.com/auth/drive.file']
FOLDER = 'application/vnd.google-apps.folder'


def service_for(credentials):
    return build('drive', 'v3', http=AuthorizedHttp(credentials, http=httplib2.Http(timeout=30)), cache_discovery=False)


@login_required
@require_POST
def connect(request):
    if not request.user.is_superuser:
        raise PermissionDenied
    if not all([settings.GOOGLE_CLIENT_ID, settings.GOOGLE_CLIENT_SECRET,
                settings.GOOGLE_DRIVE_REDIRECT_URI, settings.TOKEN_ENCRYPTION_KEY]):
        messages.error(request, 'Configure as credenciais Google, o retorno do Drive e a chave de cifragem no servidor.')
        return redirect('dashboard')
    oauth = flow()
    url, state = oauth.authorization_url(access_type='offline', prompt='consent')
    request.session['drive_state'] = state
    request.session['drive_started_at'] = timezone.now().timestamp()
    return redirect(url)


def flow(state=None):
    return Flow.from_client_config({'web': {
        'client_id': settings.GOOGLE_CLIENT_ID, 'client_secret': settings.GOOGLE_CLIENT_SECRET,
        'auth_uri': 'https://accounts.google.com/o/oauth2/auth',
        'token_uri': 'https://oauth2.googleapis.com/token',
    }}, scopes=SCOPES, state=state, redirect_uri=settings.GOOGLE_DRIVE_REDIRECT_URI)


@login_required
def callback(request):
    if not request.user.is_superuser:
        raise PermissionDenied
    expected = request.session.pop('drive_state', None)
    started = request.session.pop('drive_started_at', 0)
    if not expected or not secrets.compare_digest(expected, request.GET.get('state', '')) or timezone.now().timestamp() - started > 600:
        raise PermissionDenied('Ligação expirada ou inválida.')
    try:
        oauth = flow(expected)
        oauth.fetch_token(code=request.GET.get('code', ''), timeout=30)
        if not oauth.credentials.refresh_token or not oauth.credentials.has_scopes(SCOPES):
            raise ValueError('Falta refresh token')
        existing = DriveConnection.objects.filter(key='office').first()
        # Reconnecting another account must not strand existing client folders.
        if existing and existing.root_folder_id:
            service_for(oauth.credentials).files().get(fileId=existing.root_folder_id, fields='id').execute()
        encrypted = Fernet(settings.TOKEN_ENCRYPTION_KEY.encode()).encrypt(oauth.credentials.to_json().encode()).decode()
        DriveConnection.objects.update_or_create(key='office', defaults={'encrypted_credentials': encrypted})
    except Exception:
        messages.error(request, 'Não foi possível ligar o Drive. Se já existem pastas, volte a autorizar a mesma conta Google.')
    else:
        messages.success(request, 'Google Drive ligado. A pasta HIMP será criada ao preparar a primeira pasta de cliente.')
    return redirect('dashboard')


def get_service(connection):
    cipher = Fernet(settings.TOKEN_ENCRYPTION_KEY.encode())
    credentials = Credentials.from_authorized_user_info(json.loads(cipher.decrypt(connection.encrypted_credentials.encode())), scopes=SCOPES)
    if credentials.expired and credentials.refresh_token:
        transport = Request()
        credentials.refresh(lambda *args, **kwargs: transport(*args, **{**kwargs, 'timeout': 30}))
        connection.encrypted_credentials = cipher.encrypt(credentials.to_json().encode()).decode()
        connection.save(update_fields=['encrypted_credentials', 'updated_at'])
    return service_for(credentials)


def find(files, query):
    result = files.list(q=query + ' and trashed = false', spaces='drive', fields='files(id)', pageSize=2).execute()['files']
    if len(result) > 1:
        raise ValueError('Referências duplicadas no Drive; peça ao administrador para verificar as pastas.')
    return result[0]['id'] if result else None


def folder_name(client):
    name = ' '.join((client.nome_completo or 'Sem nome').split())
    return f'{client.pk} - {name}'[:200]


def ensure_folder(files, connection, client):
    if not connection.root_folder_id:
        root = find(files, "mimeType = 'application/vnd.google-apps.folder' and appProperties has { key='himpRoot' and value='1' }")
        if not root:
            root = files.create(body={'name': 'HIMP', 'mimeType': FOLDER, 'appProperties': {'himpRoot': '1'}}, fields='id').execute()['id']
        connection.root_folder_id = root
        connection.save(update_fields=['root_folder_id'])
    root = files.get(fileId=connection.root_folder_id, fields='id,trashed').execute()
    if root.get('trashed'):
        raise ValueError('A pasta principal está no lixo.')
    name = folder_name(client)
    if not client.drive_folder_id:
        folder = find(files, f"'{connection.root_folder_id}' in parents and mimeType = '{FOLDER}' and appProperties has {{ key='himpClient' and value='{client.pk}' }}")
        if not folder:
            folder = files.create(body={'name': name, 'mimeType': FOLDER, 'parents': [connection.root_folder_id],
                                        'appProperties': {'himpClient': str(client.pk)}}, fields='id').execute()['id']
        client.drive_folder_id = folder
        client.save(update_fields=['drive_folder_id'])
    folder = files.get(fileId=client.drive_folder_id, fields='id,name,trashed').execute()
    if folder.get('trashed'):
        raise ValueError('A pasta do cliente está no lixo.')
    if folder.get('name') != name:
        files.update(fileId=client.drive_folder_id, body={'name': name}, fields='id').execute()
    return client.drive_folder_id


@transaction.atomic
def create_client_folder(client_id):
    connection = DriveConnection.objects.select_for_update().get(key='office')
    client = Cliente.objects.select_for_update().get(pk=client_id)
    return ensure_folder(get_service(connection).files(), connection, client)


@transaction.atomic
def upload_document(document_id, content, filename, mimetype):
    # Serialize office folder creation and retries. appProperties recovers remote
    # success if the local commit failed, without uploading duplicate documents.
    connection = DriveConnection.objects.select_for_update().get(key='office')
    document = DocumentoCliente.objects.select_for_update().get(pk=document_id)
    client = Cliente.objects.select_for_update().get(pk=document.cliente_id)
    if document.drive_file_id:
        raise ValueError('Este registo já tem um ficheiro. Crie outro registo para uma nova versão.')
    files = get_service(connection).files()
    folder = ensure_folder(files, connection, client)
    file_id = find(files, f"'{folder}' in parents and appProperties has {{ key='himpDocument' and value='{document.pk}' }}")
    digest = sha256(content).hexdigest()
    if file_id:
        existing = files.get(fileId=file_id, fields='name,appProperties').execute()
        if existing.get('appProperties', {}).get('himpHash') != digest:
            raise ValueError('Existe um envio anterior com conteúdo diferente. Verifique a pasta do cliente.')
        filename = existing['name']
    if not file_id:
        media = MediaIoBaseUpload(BytesIO(content), mimetype=mimetype, resumable=False)
        file_id = files.create(body={'name': filename, 'parents': [folder],
            'appProperties': {'himpDocument': str(document.pk), 'himpHash': digest}}, media_body=media, fields='id').execute()['id']
    document.drive_file_id = file_id
    document.drive_filename = filename
    document.entregue = True
    document.save(update_fields=['drive_file_id', 'drive_filename', 'entregue'])
    return document
