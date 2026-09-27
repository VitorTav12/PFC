from datetime import datetime

from app.extensions import db


class AuditoriaLog(db.Model):
    __tablename__ = 'auditoria_log'

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=True)
    acao = db.Column(db.String(50), nullable=False)
    detalhes = db.Column(db.Text, nullable=False)
    data_horario = db.Column(db.DateTime, default=datetime.now)

    @staticmethod
    def registrar(usuario_id, acao, detalhes):
        log = AuditoriaLog(usuario_id=usuario_id, acao=acao, detalhes=detalhes)
        db.session.add(log)