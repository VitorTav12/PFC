import os

from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.getenv('SECRET_KEY')
    NOME_ESCOLA = os.getenv('NOME_ESCOLA', 'Creche Pequenos Girassóis')
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = os.getenv('SQLALCHEMY_ECHO') == '1'

    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads', 'autorizados')
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024
    
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    SESSION_COOKIE_SECURE = os.getenv('COOKIE_SECURE') == '1'
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_SAMESITE = 'Lax'
    REMEMBER_COOKIE_SECURE = os.getenv('COOKIE_SECURE') == '1'
    REMEMBER_COOKIE_DURATION = timedelta(days=30)  

    BREVO_API_KEY = os.getenv('BREVO_API_KEY')
    BREVO_API_URL = os.getenv('BREVO_API_URL', 'https://api.brevo.com/v3/smtp/email')
    EMAIL_REMETENTE = os.getenv('EMAIL_REMETENTE')
    EMAIL_REMETENTE_NOME = os.getenv('EMAIL_REMETENTE_NOME', NOME_ESCOLA)