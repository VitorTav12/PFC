from datetime import datetime

from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from app.extensions import db, login_manager


class Usuario(UserMixin, db.Model):
    __tablename__ = 'usuario'

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    senha = db.Column(db.String(255), nullable=False)
    nivel_acesso = db.Column(db.String(20), nullable=False) 
    criado_em = db.Column(db.DateTime, default=datetime.now)

    responsavel = db.relationship('Responsavel', backref='usuario', uselist=False, cascade="all, delete-orphan")
    logs = db.relationship('AuditoriaLog', backref='usuario')

    def set_senha(self, senha_texto_puro):
        self.senha = generate_password_hash(senha_texto_puro)

    def checar_senha(self, senha_digitada):
        if not self.senha:
            return False
        try:
            return check_password_hash(self.senha, senha_digitada)
        except Exception:
            return False


@login_manager.user_loader
def load_user(user_id):
    return Usuario.query.get(int(user_id))
