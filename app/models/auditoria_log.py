from datetime import datetime, timedelta

from sqlalchemy import func

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

    @staticmethod
    def recentes(limite=30):
        return AuditoriaLog.query.order_by(AuditoriaLog.id.desc()).limit(limite).all()

    @staticmethod
    def contar(acao, desde):
        return AuditoriaLog.query.filter(
            AuditoriaLog.acao == acao,
            AuditoriaLog.data_horario >= desde
        ).count()

    @staticmethod
    def contagem_diaria(acao, dias=7):
        hoje = datetime.now().date()
        inicio = hoje - timedelta(days=dias - 1)
        dia = func.date(AuditoriaLog.data_horario)

        linhas = (db.session.query(dia, func.count(AuditoriaLog.id))
                  .filter(AuditoriaLog.acao == acao, dia >= inicio)
                  .group_by(dia)
                  .all())
        por_dia = {data: total for data, total in linhas}

        return [por_dia.get(inicio + timedelta(days=i), 0) for i in range(dias)]