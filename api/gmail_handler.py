from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
import base64
from datetime import datetime
import json

class GmailHandler:
    def __init__(self, service_account_json):
        """Inicializar con credenciales de Google Cloud"""
        self.service = self._authenticate(service_account_json)
        self.emails_processed = 0
    
    def _authenticate(self, service_account_json):
        """Autenticar con Gmail API usando service account"""
        credentials = Credentials.from_service_account_info(
            service_account_json,
            scopes=['https://www.googleapis.com/auth/gmail.readonly']
        )
        return build('gmail', 'v1', credentials=credentials)
    
    def get_emails_from_last_hour(self, max_results=20):
        """Obtener correos de la ultima hora"""
        try:
            results = self.service.users().messages().list(
                userId='me',
                q='is:unread newer_than:1h',
                maxResults=max_results
            ).execute()
            
            messages = results.get('messages', [])
            emails = []
            
            for msg in messages:
                email_data = self._extract_email_data(msg['id'])
                if email_data:
                    emails.append(email_data)
            
            self.emails_processed += len(emails)
            return emails
        except Exception as e:
            print(f"Error fetching emails: {e}")
            return []
    
    def _extract_email_data(self, message_id):
        """Extraer datos del correo"""
        try:
            message = self.service.users().messages().get(
                userId='me',
                id=message_id,
                format='full'
            ).execute()
            
            headers = message['payload']['headers']
            body = self._get_body(message['payload'])
            
            return {
                'id': message_id,
                'from': self._get_header(headers, 'From'),
                'subject': self._get_header(headers, 'Subject'),
                'body': body[:500],
                'date': self._get_header(headers, 'Date')
            }
        except Exception as e:
            print(f"Error extracting email {message_id}: {e}")
            return None
    
    def _get_header(self, headers, name):
        """Obtener valor del header"""
        return next((h['value'] for h in headers if h['name'] == name), 'N/A')
    
    def _get_body(self, payload):
        """Extraer cuerpo del mensaje"""
        if 'parts' in payload:
            return self._get_body(payload['parts'][0])
        elif 'body' in payload and 'data' in payload['body']:
            try:
                return base64.urlsafe_b64decode(payload['body']['data']).decode('utf-8')
            except:
                return 'Unable to decode'
        return 'No body'
