import os
import json
import base64
from dotenv import load_dotenv

load_dotenv()

from google.auth.transport.requests import Request
from google.oauth2.service_account import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google_auth_httplib2 import AuthorizedHttp
import httplib2

from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

class GmailService:
    """Service to send emails using Gmail API"""
    
    SCOPES = ['https://www.googleapis.com/auth/gmail.send']
    
    def __init__(self, credentials_path: str = "gmail-credentials.json"):
        self.credentials_path = credentials_path
        self.service = self._build_service()
    
    def _build_service(self):
        """Builds the Gmail service"""
        # In Cloud Run / headless environments, skip interactive OAuth entirely.
        if os.getenv("SKIP_GMAIL_OAUTH"):
            print("Skipping Gmail OAuth flow because SKIP_GMAIL_OAUTH is set.")
            return None

        try:
            import google.auth.transport.requests
            from google.oauth2.credentials import Credentials as OAuth2Credentials
            from googleapiclient.discovery import build
            
            # Intentar cargar credenciales guardadas
            creds = None
            try:
                with open('token.json', 'r') as token:
                    creds_data = json.load(token)
                    creds = OAuth2Credentials.from_authorized_user_info(creds_data)
            except FileNotFoundError:
                # Si no existen, crear flujo de autenticación
                gmail_client_id = os.getenv("GMAIL_CLIENT_ID")
                gmail_client_secret = os.getenv("GMAIL_CLIENT_SECRET")
                gcp_project_id = os.getenv("GCP_PROJECT_ID")
                
                client_config = {
                    "installed": {
                        "client_id": gmail_client_id,
                        "client_secret": gmail_client_secret,
                        "project_id": gcp_project_id,
                        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                        "token_uri": "https://oauth2.googleapis.com/token",
                        "redirect_uris": ["http://localhost"]
                    }
                }
                flow = InstalledAppFlow.from_client_config(client_config, self.SCOPES)
                creds = flow.run_local_server(port=0)
                
                with open('token.json', 'w') as token:
                    token.write(creds.to_json())
            
            return build('gmail', 'v1', credentials=creds)
        except Exception as e:
            print(f"Error initializing Gmail: {e}")
            return None
    
    def send_email(self, to_email: str, subject: str, body: str, is_html: bool = True):
        """Sends an email using Gmail API"""
        if not self.service:
            print("Gmail service not initialized")
            return False
        
        try:
            # Crear mensaje
            message = MIMEMultipart('alternative')
            message['to'] = to_email
            message['subject'] = subject
            
            # Agregar contenido
            if is_html:
                message.attach(MIMEText(body, 'html'))
            else:
                message.attach(MIMEText(body, 'plain'))
            
            # Codificar mensaje
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
            
            # Enviar
            self.service.users().messages().send(
                userId='me',
                body={'raw': raw_message}
            ).execute()
            
            print(f"Email sent successfully to {to_email}")
            return True
        
        except Exception as e:
            print(f"Error sending email: {e}")
            return False
    
    def get_registration_email_html(self, user_name: str):
        """Generates the HTML body for the platform registration welcome email"""
        return f"""
        <html>
            <body style="font-family: Arial, sans-serif; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h1 style="color: #4CAF50;">¡Bienvenido/a, {user_name}!</h1>
                    <p>Te has registrado con éxito en la plataforma <strong>Tutor-Learning</strong>.</p>
                    <p>Ya puedes empezar a explorar los cursos disponibles y apuntarte a aquellos que más te interesen.</p>
                    <p>Si tienes alguna duda, no dudes en contactarnos.</p>
                    <br>
                    <p style="color: #666; font-size: 12px;">
                        Este es un correo automático de la plataforma Tutor-Learning.
                    </p>
                </div>
            </body>
        </html>
        """

    def get_enrollment_email_html(self, user_name: str, course_title: str):
        """Generates the HTML body for the course enrollment welcome email"""
        return f"""
        <html>
            <body style="font-family: Arial, sans-serif; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h1 style="color: #4CAF50;">¡Bienvenido/a, {user_name}!</h1>
                    <p>Te has matriculado con éxito en el curso:</p>
                    <h2 style="color: #2196F3;">{course_title}</h2>
                    <p>Esperamos que disfrutes del contenido y tengas una excelente experiencia de aprendizaje.</p>
                    <p>Si tienes cualquier duda, el profesor está a tu disposición.</p>
                    <br>
                    <p style="color: #666; font-size: 12px;">
                        Este es un correo automático de la plataforma Tutor-Learning.
                    </p>
                </div>
            </body>
        </html>
        """

    def send_welcome_email(self, user_email: str, user_name: str, course_title: str):
        """Sends a welcome email to an enrolled student (legacy direct send)"""
        subject = f"Welcome to {course_title}!"
        body = self.get_enrollment_email_html(user_name, course_title)
        return self.send_email(user_email, subject, body, is_html=True)

# Global instance of Gmail service
gmail_service = GmailService()
