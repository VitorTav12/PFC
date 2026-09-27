import hashlib
import hmac
import secrets
from datetime import datetime, timedelta

from flask import current_app

from app.extensions import db

VALIDADE_CODIGO = timedelta(minutes=10)
MAX_TENTATIVAS = 5
INTERVALO_REENVIO = timedelta(seconds=60)


class Codigo2FA(db.Model):
    __tablename__ = 'codigo_2fa'

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    codigo_hash = db.Column(db.String(64), nullable=False)
    expira_em = db.Column(db.DateTime, nullable=False)
    usado_em = db.Column(db.DateTime, nullable=True)
    tentativas = db.Column(db.Integer, nullable=False, default=0)
    criado_em = db.Column(db.DateTime, default=datetime.now)

    @staticmethod
    def calcular_hash(codigo):
        chave = current_app.config['SECRET_KEY'].encode('utf-8')
        return hmac.new(chave, codigo.encode('utf-8'), hashlib.sha256).hexdigest()

    @staticmethod
    def gerar(usuario_id):
        agora = datetime.now()

        Codigo2FA.query.filter_by(usuario_id=usuario_id, usado_em=None).update({'usado_em': agora})

        codigo = f'{secrets.randbelow(1_000_000):06d}'
        db.session.add(Codigo2FA(
            usuario_id=usuario_id,
            codigo_hash=Codigo2FA.calcular_hash(codigo),
            expira_em=agora + VALIDADE_CODIGO,
            tentativas=0
        ))
        return codigo

    @staticmethod
    def atual(usuario_id):
        return (Codigo2FA.query
                .filter_by(usuario_id=usuario_id, usado_em=None)
                .order_by(Codigo2FA.id.desc())
                .first())

    def valido(self):
        return self.usado_em is None and datetime.now() <= self.expira_em and self.tentativas < MAX_TENTATIVAS

    def pode_reenviar(self):
        return datetime.now() - self.criado_em >= INTERVALO_REENVIO

    def conferir(self, codigo_digitado):
        if hmac.compare_digest(self.codigo_hash, Codigo2FA.calcular_hash(codigo_digitado)):
            self.usado_em = datetime.now()
            return True

        self.tentativas += 1
        if self.tentativas >= MAX_TENTATIVAS:
            self.usado_em = datetime.now()
        return False