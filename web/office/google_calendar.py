import json
import secrets
from datetime import timedelta, timezone as datetime_timezone

import httplib2
from cryptography.fernet import Fernet
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.utils import timezone
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_httplib2 import AuthorizedHttp
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build

from .models import CalendarConnection, Configuration

SCOPES = ['https://www.googleapis.com/auth/calendar.events']


def flow(state=None):
    if not all([settings.GOOGLE_CLIENT_ID, settings.GOOGLE_CLIENT_SECRET, settings.GOOGLE_REDIRECT_URI, settings.TOKEN_ENCRYPTION_KEY]):
        raise ValueError('Integração Google não configurada')
    return Flow.from_client_config({'web': {
        'client_id': settings.GOOGLE_CLIENT_ID, 'client_secret': settings.GOOGLE_CLIENT_SECRET,
        'auth_uri': 'https://accounts.google.com/o/oauth2/auth',
        'token_uri': 'https://oauth2.googleapis.com/token',
    }}, scopes=SCOPES, state=state, redirect_uri=settings.GOOGLE_REDIRECT_URI)


@login_required
def connect(request):
    if not request.user.is_superuser:
        raise PermissionDenied
    if request.method != 'POST':
        from django.http import HttpResponseNotAllowed
        return HttpResponseNotAllowed(['POST'])
    try:
        oauth = flow()
        url, state = oauth.authorization_url(access_type='offline', prompt='consent')
    except ValueError:
        messages.error(request, 'Configure as credenciais Google Web e a chave de cifragem no servidor.')
        return redirect('dashboard')
    request.session['google_state'] = state
    request.session['google_started_at'] = timezone.now().timestamp()
    return redirect(url)


@login_required
def callback(request):
    if not request.user.is_superuser:
        raise PermissionDenied
    expected = request.session.pop('google_state', None)
    started = request.session.pop('google_started_at', 0)
    supplied = request.GET.get('state', '')
    if not expected or not secrets.compare_digest(expected, supplied) or timezone.now().timestamp() - started > 600:
        raise PermissionDenied('Ligação expirada ou inválida.')
    try:
        oauth = flow(expected)
        # Exchange only the returned code; never trust the request Host for the callback URL.
        oauth.fetch_token(code=request.GET.get('code', ''), timeout=15)
        if not oauth.credentials.refresh_token:
            raise ValueError('Falta refresh token')
        encrypted = Fernet(settings.TOKEN_ENCRYPTION_KEY.encode()).encrypt(oauth.credentials.to_json().encode()).decode()
        CalendarConnection.objects.update_or_create(key='office', defaults={'encrypted_credentials': encrypted})
    except Exception:
        messages.error(request, 'Não foi possível ligar o Google Calendar. Tente novamente.')
    else:
        messages.success(request, 'Google Calendar ligado com sucesso.')
    return redirect('dashboard')


def sync_event(event):
    connection = CalendarConnection.objects.get(key='office')
    cipher = Fernet(settings.TOKEN_ENCRYPTION_KEY.encode())
    credentials = Credentials.from_authorized_user_info(json.loads(cipher.decrypt(connection.encrypted_credentials.encode())), scopes=SCOPES)
    if credentials.expired and credentials.refresh_token:
        transport = Request()
        credentials.refresh(lambda *args, **kwargs: transport(*args, **{**kwargs, 'timeout': 15}))
        connection.encrypted_credentials = cipher.encrypt(credentials.to_json().encode()).decode()
        connection.save()
    duration = Configuration.objects.get(category=Configuration.Category.DURATION, label=event.duracao)
    if not duration.minutes or not event.data_inicio:
        raise ValueError('Data/duração inválida')
    start = timezone.localtime(event.data_inicio)
    body = {
        'summary': event.titulo, 'description': event.descricao or '',
        'start': {'dateTime': start.isoformat(), 'timeZone': settings.TIME_ZONE},
        'end': {'dateTime': timezone.localtime(start.astimezone(datetime_timezone.utc) + timedelta(minutes=duration.minutes)).isoformat(), 'timeZone': settings.TIME_ZONE},
    }
    service = build('calendar', 'v3', http=AuthorizedHttp(credentials, http=httplib2.Http(timeout=15)), cache_discovery=False)
    # Deterministic ID makes retry safe when Google succeeded but saving locally failed.
    event_id = event.google_event_id or f'himp{event.pk:x}'
    events = service.events()
    from googleapiclient.errors import HttpError
    try:
        events.get(calendarId=settings.GOOGLE_CALENDAR_ID, eventId=event_id).execute()
    except HttpError as exc:
        if exc.resp.status != 404:
            raise
        result = events.insert(calendarId=settings.GOOGLE_CALENDAR_ID, body={**body, 'id': event_id}).execute()
    else:
        result = events.update(calendarId=settings.GOOGLE_CALENDAR_ID, eventId=event_id, body=body).execute()
    event.google_event_id = result['id']
    event.save(update_fields=['google_event_id'])
