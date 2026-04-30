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
    
    def send_welcome_email(self, user_email: str, user_name: str, course_title: str):
        """Sends a welcome email to an enrolled student"""
        subject = f"Welcome to {course_title}!"
        
        body = f"""
        <html>
            <body style="font-family: Arial, sans-serif; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h1 style="color: #4CAF50;">Welcome, {user_name}!</h1>
                    <p>You have successfully enrolled in the course:</p>
                    <h2 style="color: #2196F3;">{course_title}</h2>
                    <p>We hope you enjoy the content and have an excellent learning experience.</p>
                    <p>If you have any questions, feel free to contact us.</p>
                    <br>
                    <p style="color: #666; font-size: 12px;">
                        This is an automated email from the Tutor-Learning Platform
                    </p>
                </div>
            </body>
        </html>
        """
        
        return self.send_email(user_email, subject, body, is_html=True)

# Global instance of Gmail service
gmail_service = GmailService()
