from datetime import datetime

from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from app.extensions import db, login_manager
from app.models.aceite_termo import VERSAO_TERMOS


class Usuario(UserMixin, db.Model):
    __tablename__ = 'usuario'

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    senha = db.Column(db.String(255), nullable=False)
    nivel_acesso = db.Column(db.String(20), nullable=False) # 'secretaria', 'diretoria', 'pais'
    precisa_trocar_senha = db.Column(db.Boolean, nullable=False, default=False)
    criado_em = db.Column(db.DateTime, default=datetime.now)

    responsavel = db.relationship('Responsavel', backref='usuario', uselist=False, cascade="all, delete-orphan")
    logs = db.relationship('AuditoriaLog', backref='usuario')
    aceites = db.relationship('AceiteTermo', backref='usuario')

    def set_senha(self, senha_texto_puro):
        self.senha = generate_password_hash(senha_texto_puro)

    def checar_senha(self, senha_digitada):
        if not self.senha:
            return False
        try:
            return check_password_hash(self.senha, senha_digitada)
        except Exception:
            return False

    def aceitou_termos_atuais(self):
        return any(aceite.versao == VERSAO_TERMOS for aceite in self.aceites)

    def pendente_primeiro_acesso(self):
        if self.nivel_acesso != 'pais':
            return False
        return self.precisa_trocar_senha or not self.aceitou_termos_atuais()

    @staticmethod
    def validar_nova_senha(senha, confirmacao):
        if len(senha) < 8:
            return 'A nova senha deve ter pelo menos 8 caracteres.'
        if not any(c.isalpha() for c in senha) or not any(c.isdigit() for c in senha):
            return 'A nova senha deve ter letras e números.'
        if senha != confirmacao:
            return 'A confirmação não é igual à nova senha.'
        return None


@login_manager.user_loader
def load_user(user_id):
    return Usuario.query.get(int(user_id))
