import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

load_dotenv()


class GmailService:
    """Service to send emails using Gmail SMTP with App Password"""

    def __init__(self):
        self.sender_email = os.getenv("GMAIL_SENDER_EMAIL")
        self.app_password = os.getenv("GMAIL_APP_PASSWORD")

        if self.sender_email and self.app_password:
            print(f"Gmail SMTP service initialized for {self.sender_email}")
        else:
            print("WARNING: Gmail SMTP credentials not configured. Emails will not be sent.")

    def send_email(self, to_email: str, subject: str, body: str, is_html: bool = True):
        """Sends an email using Gmail SMTP"""
        if not self.sender_email or not self.app_password:
            return False, "Gmail SMTP credentials (GMAIL_SENDER_EMAIL or GMAIL_APP_PASSWORD) are not set in the environment variables."

        try:
            # Create message
            message = MIMEMultipart('alternative')
            message['From'] = f"Tutor-Learning <{self.sender_email}>"
            message['To'] = to_email
            message['Subject'] = subject

            # Add content
            if is_html:
                message.attach(MIMEText(body, 'html'))
            else:
                message.attach(MIMEText(body, 'plain'))

            # Connect to Gmail SMTP and send
            with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
                server.login(self.sender_email, self.app_password)
                server.sendmail(self.sender_email, to_email, message.as_string())

            return True, ""

        except Exception as e:
            print(f"Error sending email: {e}")
            return False, str(e)

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
