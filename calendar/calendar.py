import tkinter as tk
from tkinter import messagebox
from google.auth.transport.requests import Request
import os.path
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from datetime import datetime, timedelta, timezone
import pytz
import os
import sys

# Escopos necessários
SCOPES = [
    'https://www.googleapis.com/auth/calendar',
    'https://www.googleapis.com/auth/userinfo.email',
    'https://www.googleapis.com/auth/userinfo.profile',
    'openid'
]

def get_token_path():
    home = os.path.expanduser("~")
    app_dir = os.path.join(os.path.expanduser("~"), "Desktop", "Documentos_Gerados")
    os.makedirs(app_dir, exist_ok=True)
    return os.path.join(app_dir, "token.json")


def resource_path(relative_path):
    if hasattr(sys, "_MEIPASS"):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.abspath(os.path.dirname(__file__))
    return os.path.join(base_path, relative_path)

def autenticar_google():
    creds = None
    
    token_path = get_token_path()
    credentials_path = resource_path("Calendar/credentials.json")

    # Arquivo token.json salva o token de acesso
    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)
    
    # Se não houver credenciais válidas, faça login
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
            creds = flow.run_local_server(port=0)
        
        # Salva o token para futuras execuções
        with open(token_path, 'w') as token:
            token.write(creds.to_json())
    
    return creds



def preparar_evento_para_google(evento, titulo_atual=None):
    """
    Converte um dicionário de evento para os parâmetros da função criar_evento.
    """
    # pega os valores
    Titulo = evento.get('titulo')
    if Titulo:
        Titulo = Titulo.upper()
    else:
        Titulo = titulo_atual.upper()  # mantém o título atual se não houver alteração

    Descricao = evento.get('descricao', None)
    DataInicio = evento['data_inicio']

    # calcula DataFim com base na duração
    duracao_str = evento.get('duracao', '30 minutos')
    if 'minuto' in duracao_str:
        minutos = int(duracao_str.split()[0])
        delta = timedelta(minutes=minutos)
    elif 'Hora' in duracao_str:
        horas = int(duracao_str.split()[0])
        delta = timedelta(hours=horas)
    else:
        delta = timedelta(minutes=30)  # padrão

    dt_inicio = datetime.fromisoformat(DataInicio)
    dt_fim = dt_inicio + delta
    DataFim = dt_fim.isoformat()

    return Titulo, Descricao, DataInicio, DataFim



def criar_evento(Titulo, Descricao, DataInicio, DataFim, emails=None, motivo=None):
    try:
        lisbon = pytz.timezone("Europe/Lisbon")

        DataInicio_dt = lisbon.localize(datetime.fromisoformat(DataInicio))
        DataFim_dt = lisbon.localize(datetime.fromisoformat(DataFim))

        creds = autenticar_google()
        service = build('calendar', 'v3', credentials=creds)

        evento = {
            'summary': Titulo,
            'description': Descricao,
            'start': {
                'dateTime': DataInicio_dt.isoformat(),
                'timeZone': 'Europe/Lisbon',
            },
            'end': {
                'dateTime': DataFim_dt.isoformat(),
                'timeZone': 'Europe/Lisbon',
            },
        }

        # 🔹 Se motivo for "Atendimento em Loja Externa", usa cor laranja (colorId = 6)
        if motivo and motivo.strip().lower() == "atendimento em loja externa".lower():
            evento['colorId'] = '2'
        if motivo and motivo.strip().lower() == "consulta".lower():
            evento['colorId'] = '1'
        else:
            evento['colorId'] = '4'

        # Se houver lista de convidados
        if emails:
            evento['attendees'] = [{'email': e} for e in (emails if isinstance(emails, list) else [emails])]

        evento = service.events().insert(
            calendarId='primary',
            body=evento,
            sendUpdates='all' if emails else 'none'
        ).execute()

        return evento

    except Exception as e:
        messagebox.showerror("Erro", str(e))
        print("Erro ao criar evento:", e)
        return None




def editar_evento(id, Titulo=None, Descricao=None, DataInicio=None, DataFim=None, email=None, motivo=None):
    try:
        creds = autenticar_google()
        service = build('calendar', 'v3', credentials=creds)

        # pega o evento existente
        evento = service.events().get(calendarId='primary', eventId=id).execute()

        # atualiza os campos recebidos
        if Titulo: 
            evento['summary'] = Titulo
        if Descricao: 
            evento['description'] = Descricao
        if DataInicio: 
            evento['start']['dateTime'] = DataInicio
        if DataFim: 
            evento['end']['dateTime'] = DataFim
        if email:
            # atualiza os convidados
            if 'attendees' not in evento:
                evento['attendees'] = []
            evento['attendees'].append({'email': email})

        # 🔹 Define cor laranja se motivo for "Atendimento em Loja Externa"
        if motivo and motivo.strip().lower() == "atendimento em loja externa".lower():
            evento['colorId'] = '2'
        if motivo and motivo.strip().lower() == "consulta":
            evento['colorId'] = '1'
        else:
            evento['colorId'] = '4' 

        # atualiza no Google Calendar e envia notificação para convidados existentes
        atualizado = service.events().update(
            calendarId='primary',
            eventId=id,
            body=evento,
            sendUpdates='all'  # notifica todos os convidados já cadastrados
        ).execute()

        return atualizado
        
    except Exception as e:
        messagebox.showerror("Erro", str(e))
        return None



def deletar_evento(id):
    try:
        creds = autenticar_google()
        service = build('calendar', 'v3', credentials=creds)

        service.events().delete(calendarId='primary', eventId=id, sendUpdates='all').execute()

        #messagebox.showinfo("Sucesso", f"Evento {id} deletado com sucesso!")
    except Exception as e:
        messagebox.showerror("Erro", str(e))

def listar_eventos_proximos_15_dias():
    try:
        creds = autenticar_google()
        service = build('calendar', 'v3', credentials=creds)

        agora = datetime.now(timezone.utc)
        daqui_15_dias = agora + timedelta(days=15)

        eventos_resultado = service.events().list(
            calendarId='primary',
            timeMin=agora.isoformat(),
            timeMax=daqui_15_dias.isoformat(),
            singleEvents=True,      # expande eventos recorrentes
            orderBy='startTime'     # ordena pela data de início
        ).execute()

        eventos = eventos_resultado.get('items', [])

        if not eventos:
            messagebox.showinfo("Eventos", "Nenhum evento nos próximos 15 dias.")
            return

        lista = ""
        for evento in eventos:
            inicio = evento['start'].get('dateTime', evento['start'].get('date'))
            fim = evento['end'].get('dateTime', evento['end'].get('date'))
            titulo = evento.get('summary', "Sem título")
            lista += f"- {titulo}\n  Início: {inicio}\n  Fim: {fim}\n\n"

        messagebox.showinfo("Eventos", lista)

    except Exception as e:
        messagebox.showerror("Erro", str(e))

