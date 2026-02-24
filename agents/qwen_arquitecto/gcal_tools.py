import os
import datetime
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

SCOPES = ['https://www.googleapis.com/auth/calendar']

def get_calendar_service():
    """Builds and returns the Google Calendar service using credentials."""
    creds_path = os.getenv('GOOGLE_CALENDAR_CREDENTIALS_PATH')
    if not creds_path:
        raise ValueError("La variable de entorno GOOGLE_CALENDAR_CREDENTIALS_PATH no está configurada. Por favor, añádela a tu archivo .env con la ruta absoluta al JSON de credenciales de Google.")
    
    if not os.path.exists(creds_path):
        raise FileNotFoundError(f"No se encontró el archivo de credenciales de Google en la ruta proporcionada: {creds_path}")

    creds = Credentials.from_service_account_file(creds_path, scopes=SCOPES)
    service = build('calendar', 'v3', credentials=creds)
    return service

def consultar_agenda() -> str:
    """
    Obtiene los eventos programados en el calendario para las próximas 24 horas.
    Retorna un texto formateado con los eventos y sus horarios.
    """
    try:
        service = get_calendar_service()
        ahora = datetime.datetime.utcnow()
        manana = ahora + datetime.timedelta(days=1)
        
        time_min = ahora.isoformat() + 'Z'
        time_max = manana.isoformat() + 'Z'
        calendar_id = os.getenv('GOOGLE_CALENDAR_ID', 'primary')
        
        events_result = service.events().list(
            calendarId=calendar_id, 
            timeMin=time_min, 
            timeMax=time_max,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        events = events_result.get('items', [])

        if not events:
            return "No tienes eventos programados para las próximas 24 horas."

        resultado = ["📅 **Eventos en las próximas 24 horas:**\n"]
        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            end = event['end'].get('dateTime', event['end'].get('date'))
            summary = event.get('summary', 'Sin Título')
            resultado.append(f"- **{summary}**\n  Inicio: {start}\n  Fin: {end}\n")
            
        return "\n".join(resultado)
        
    except ValueError as ve:
        return f"⚠️ Error de Configuración de Calendario: {str(ve)}"
    except Exception as e:
        return f"Error al consultar la agenda: {str(e)}"

def agendar_revision(titulo: str, descripcion: str, inicio_iso: str, fin_iso: str) -> str:
    """
    Programa un nuevo evento en el calendario (ej: para revisar artefactos).
    Verifica primero que no se solape con otros eventos existentes en ese horario.
    Argumentos:
        titulo: El título del evento.
        descripcion: La descripción o detalles del evento.
        inicio_iso: Fecha y hora de inicio en formato ISO 8601 (ej. '2026-02-22T15:00:00Z').
        fin_iso: Fecha y hora de fin en formato ISO 8601 (ej. '2026-02-22T16:00:00Z').
    """
    try:
        service = get_calendar_service()
        
        # 1. Verificar solapamiento
        calendar_id = os.getenv('GOOGLE_CALENDAR_ID', 'primary')
        
        events_result = service.events().list(
            calendarId=calendar_id, 
            timeMin=inicio_iso, 
            timeMax=fin_iso,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        events = events_result.get('items', [])
        if events:
            conflictos = [e.get('summary', 'Evento Ocupado') for e in events]
            return f"❌ No se puede agendar '{titulo}' de {inicio_iso} a {fin_iso} porque se solapa con los siguientes eventos: {', '.join(conflictos)}. Por favor, busca otro horario usando consultar_agenda."

        # 2. Crear el evento si está libre
        event = {
            'summary': titulo,
            'description': descripcion,
            'start': {
                'dateTime': inicio_iso,
                'timeZone': 'Europe/Madrid', # Or use a parameter if strictly needed, falling back to user locale
            },
            'end': {
                'dateTime': fin_iso,
                'timeZone': 'Europe/Madrid',
            }
        }

        event_result = service.events().insert(calendarId=calendar_id, body=event).execute()
        return f"✅ Evento '{titulo}' agendado correctamente.\nEnlace al evento: {event_result.get('htmlLink')}"
        
    except ValueError as ve:
         return f"⚠️ Error de Configuración de Calendario: {str(ve)}"
    except Exception as e:
        return f"Error al agendar la revisión: {str(e)}"
