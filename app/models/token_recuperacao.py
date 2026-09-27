import hashlib
import secrets
from datetime import datetime, timedelta

from app.extensions import db

VALIDADE_TOKEN = timedelta(minutes=30)


class TokenRecuperacao(db.Model):
    __tablename__ = 'token_recuperacao'

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    token_hash = db.Column(db.String(64), unique=True, nullable=False)
    expira_em = db.Column(db.DateTime, nullable=False)
    usado_em = db.Column(db.DateTime, nullable=True)
    criado_em = db.Column(db.DateTime, default=datetime.now)

    usuario = db.relationship('Usuario')

    @staticmethod
    def calcular_hash(token):
        return hashlib.sha256(token.encode('utf-8')).hexdigest()

    @staticmethod
    def gerar(usuario):
        agora = datetime.now()

        TokenRecuperacao.query.filter_by(usuario_id=usuario.id, usado_em=None).update({'usado_em': agora})

        token = secrets.token_urlsafe(32)
        registro = TokenRecuperacao(
            usuario_id=usuario.id,
            token_hash=TokenRecuperacao.calcular_hash(token),
            expira_em=agora + VALIDADE_TOKEN
        )
        db.session.add(registro)
        return token

    @staticmethod
    def buscar(token):
        return TokenRecuperacao.query.filter_by(token_hash=TokenRecuperacao.calcular_hash(token)).first()

    def valido(self):
        return self.usado_em is None and datetime.now() <= self.expira_em