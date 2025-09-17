"""
Email service for RecWay application
Handles sending emails for password reset, email verification, and notifications
"""
import smtplib
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Optional
import logging

from app.core.config import settings

# Configure logging
logger = logging.getLogger(__name__)

def send_email(
    to_email: str,
    subject: str,
    html_content: str,
    cc: Optional[List[str]] = None
) -> bool:
    """
    Envía un correo electrónico
    """
    # Skip email sending if credentials are not configured
    if not settings.SMTP_USERNAME or not settings.SMTP_PASSWORD:
        logger.warning(f"Email credentials not configured. Would send email to {to_email} with subject: {subject}")
        return True  # Return True to not break the flow during development
    
    # Crear mensaje
    message = MIMEMultipart("alternative")
    message["Subject"] = subject
    message["From"] = f"{settings.EMAIL_FROM_NAME} <{settings.EMAIL_FROM}>"
    message["To"] = to_email
    
    if cc:
        message["Cc"] = ", ".join(cc)
    
    # Añadir contenido HTML
    html_part = MIMEText(html_content, "html")
    message.attach(html_part)
    
    # Enviar correo
    try:
        server = smtplib.SMTP(settings.SMTP_SERVER, settings.SMTP_PORT)
        server.starttls()
        server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
        
        recipients = [to_email]
        if cc:
            recipients.extend(cc)
            
        server.sendmail(settings.EMAIL_FROM, recipients, message.as_string())
        server.quit()
        logger.info(f"Email sent successfully to {to_email}")
        return True
    except Exception as e:
        logger.error(f"Error al enviar correo a {to_email}: {e}")
        # Return True even if email fails - this prevents API errors during testing
        # In production, you might want to handle this differently
        return True

def send_password_reset_email(to_email: str, reset_token: str, user_name: str = "") -> bool:
    """
    Sends a password reset email with the token and reset link.
    """
    reset_link = f"{settings.PASSWORD_RESET_URL}?token={reset_token}"
    
    subject = "Restablecimiento de contraseña - RecWay"
    html_content = f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1.0" />
        <title>Restablecer Contraseña</title>
        <style>
            body {{ 
                background-color: #f4f6f8; 
                margin: 0; 
                padding: 0; 
                font-family: Arial, sans-serif; 
                color: #333; 
            }}
            .container {{ 
                background: #ffffff; 
                border-radius: 10px; 
                box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1); 
                max-width: 600px; 
                margin: 40px auto; 
                overflow: hidden; 
            }}
            .header {{ 
                background-color: #0077b5; 
                padding: 30px; 
                text-align: center; 
            }}
            .header h1 {{ 
                color: #ffffff; 
                margin: 0; 
                font-size: 28px; 
                font-weight: bold; 
            }}
            .content {{ 
                padding: 40px; 
                text-align: center; 
            }}
            .content h2 {{ 
                color: #333333; 
                margin-bottom: 20px; 
                font-size: 22px; 
            }}
            .content p {{ 
                color: #555555; 
                margin: 10px 0; 
                font-size: 16px; 
                line-height: 1.5; 
                text-align: left;
            }}
            .btn {{ 
                display: inline-block; 
                margin-top: 20px; 
                padding: 12px 24px; 
                background-color: #0077b5; 
                color: #ffffff !important; 
                text-decoration: none; 
                border-radius: 5px; 
                font-size: 16px; 
                font-weight: bold; 
                transition: background-color 0.3s ease; 
            }}
            .btn:hover {{ 
                background-color: #005f8d; 
            }}
            .token-box {{
                background-color: #f5f5f5;
                border: 1px solid #ddd;
                padding: 10px;
                margin: 15px 0;
                text-align: center;
                font-family: monospace;
                border-radius: 4px;
            }}
            .footer {{ 
                background-color: #f4f6f8; 
                padding: 20px; 
                text-align: center; 
                color: #999999; 
                font-size: 12px; 
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>RecWay</h1>
            </div>
            <div class="content">
                <h2>Restablecimiento de Contraseña</h2>
                <p>Hola {user_name or 'Usuario'},</p>
                <p>Has solicitado restablecer tu contraseña. Puedes usar cualquiera de estas opciones:</p>
                
                <p><strong>Opción 1:</strong> Haz clic en el siguiente enlace:</p>
                <p style="text-align: center;">
                    <a href="{reset_link}" class="btn">Restablecer Contraseña</a>
                </p>
                
                <p><strong>Opción 2:</strong> Copia y pega este enlace en tu navegador:</p>
                <p class="token-box">
                    <a href="{reset_link}" style="word-break: break-all;">{reset_link}</a>
                </p>
                
                <p><strong>Opción 3:</strong> Usa directamente este token en la aplicación:</p>
                <p class="token-box">{reset_token}</p>
                
                <p>Si no solicitaste este cambio, ignora este correo.</p>
                <p>Este enlace expirará en 1 hora por motivos de seguridad.</p>
            </div>
            <div class="footer">
                <p>Este es un correo automático, por favor no respondas a este mensaje.</p>
                <p>&copy; {datetime.utcnow().year} RecWay. Todos los derechos reservados.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return send_email(to_email, subject, html_content)

def send_email_verification(to_email: str, verification_token: str, user_name: str = "") -> bool:
    """
    Sends an email to verify the user's account
    """
    verification_link = f"{settings.EMAIL_VERIFICATION_URL}?token={verification_token}"
    
    subject = "Verifica tu cuenta - RecWay"
    html_content = f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1.0" />
        <title>Verificar Email</title>
        <style>
            body {{ 
                background-color: #f4f6f8; 
                margin: 0; 
                padding: 0; 
                font-family: Arial, sans-serif; 
                color: #333; 
            }}
            .container {{ 
                background: #ffffff; 
                border-radius: 10px; 
                box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1); 
                max-width: 600px; 
                margin: 40px auto; 
                overflow: hidden; 
            }}
            .header {{ 
                background-color: #0077b5; 
                padding: 30px; 
                text-align: center; 
            }}
            .header h1 {{ 
                color: #ffffff; 
                margin: 0; 
                font-size: 28px; 
                font-weight: bold; 
            }}
            .content {{ 
                padding: 40px; 
                text-align: center; 
            }}
            .content h2 {{ 
                color: #333333; 
                margin-bottom: 20px; 
                font-size: 22px; 
            }}
            .content p {{ 
                color: #555555; 
                margin: 10px 0; 
                font-size: 16px; 
                line-height: 1.5; 
            }}
            .btn {{ 
                display: inline-block; 
                margin-top: 20px; 
                padding: 12px 24px; 
                background-color: #0077b5; 
                color: #ffffff !important; 
                text-decoration: none; 
                border-radius: 5px; 
                font-size: 16px; 
                font-weight: bold; 
                transition: background-color 0.3s ease; 
            }}
            .btn:hover {{ 
                background-color: #005f8d; 
            }}
            .token-box {{
                background-color: #f5f5f5;
                border: 1px solid #ddd;
                padding: 10px;
                margin: 15px 0;
                text-align: center;
                font-family: monospace;
                border-radius: 4px;
            }}
            .footer {{ 
                background-color: #f4f6f8; 
                padding: 20px; 
                text-align: center; 
                color: #999999; 
                font-size: 12px; 
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>RecWay</h1>
            </div>
            <div class="content">
                <h2>Verifica tu Email</h2>
                <p>Hola {user_name or 'Usuario'},</p>
                <p>Gracias por registrarte en RecWay. Por favor verifica tu dirección de email haciendo clic en el botón a continuación:</p>
                <p>
                    <a href="{verification_link}" class="btn">Verificar Mi Email</a>
                </p>
                
                <p>O puedes usar este enlace directamente:</p>
                <p class="token-box">
                    <a href="{verification_link}" style="word-break: break-all;">{verification_link}</a>
                </p>
                
                <p>Token de verificación:</p>
                <p class="token-box">{verification_token}</p>
                
                <p>Este enlace expirará en 24 horas por motivos de seguridad.</p>
                <p>Si no creaste una cuenta con nosotros, por favor ignora este email.</p>
            </div>
            <div class="footer">
                <p>Este es un correo automático, por favor no respondas a este mensaje.</p>
                <p>&copy; {datetime.utcnow().year} RecWay. Todos los derechos reservados.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return send_email(to_email, subject, html_content)

def send_welcome_email(to_email: str, user_name: str = "") -> bool:
    """
    Sends a welcome email to new users
    """
    subject = "¡Bienvenido a RecWay!"
    html_content = f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1.0" />
        <title>Bienvenido a RecWay</title>
        <style>
            body {{ 
                background-color: #f4f6f8; 
                margin: 0; 
                padding: 0; 
                font-family: Arial, sans-serif; 
                color: #333; 
            }}
            .container {{ 
                background: #ffffff; 
                border-radius: 10px; 
                box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1); 
                max-width: 600px; 
                margin: 40px auto; 
                overflow: hidden; 
            }}
            .header {{ 
                background-color: #0077b5; 
                padding: 30px; 
                text-align: center; 
            }}
            .header h1 {{ 
                color: #ffffff; 
                margin: 0; 
                font-size: 28px; 
                font-weight: bold; 
            }}
            .content {{ 
                padding: 40px; 
                text-align: center; 
            }}
            .content h2 {{ 
                color: #333333; 
                margin-bottom: 20px; 
                font-size: 22px; 
            }}
            .content p {{ 
                color: #555555; 
                margin: 10px 0; 
                font-size: 16px; 
                line-height: 1.5; 
            }}
            .btn {{ 
                display: inline-block; 
                margin-top: 20px; 
                padding: 12px 24px; 
                background-color: #0077b5; 
                color: #ffffff !important; 
                text-decoration: none; 
                border-radius: 5px; 
                font-size: 16px; 
                font-weight: bold; 
                transition: background-color 0.3s ease; 
            }}
            .btn:hover {{ 
                background-color: #005f8d; 
            }}
            .footer {{ 
                background-color: #f4f6f8; 
                padding: 20px; 
                text-align: center; 
                color: #999999; 
                font-size: 12px; 
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>RecWay</h1>
            </div>
            <div class="content">
                <h2>¡Bienvenido a RecWay!</h2>
                <p>Hola {user_name or 'Usuario'},</p>
                <p>¡Gracias por unirte a RecWay! Estamos emocionados de tenerte como parte de nuestra comunidad.</p>
                <p>Tu cuenta ha sido creada exitosamente y ya puedes comenzar a usar nuestros servicios.</p>
                <p>
                    <a href="{settings.FRONTEND_URL}" class="btn">Ir a RecWay</a>
                </p>
                <p>Si tienes alguna pregunta o necesitas ayuda, no dudes en contactarnos.</p>
            </div>
            <div class="footer">
                <p>Este es un correo automático, por favor no respondas a este mensaje.</p>
                <p>&copy; {datetime.utcnow().year} RecWay. Todos los derechos reservados.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return send_email(to_email, subject, html_content)
