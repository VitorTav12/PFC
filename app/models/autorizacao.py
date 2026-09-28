from datetime import date, datetime

from app.extensions import db


class Autorizacao(db.Model):
    __tablename__ = 'autorizacao'

    id = db.Column(db.Integer, primary_key=True)
    autorizado_id = db.Column(db.Integer, db.ForeignKey('autorizado.id'), nullable=False)
    aluno_id = db.Column(db.Integer, db.ForeignKey('aluno.id'), nullable=False)
    data_inicio = db.Column(db.Date, nullable=False)
    data_fim = db.Column(db.Date, nullable=False)
    criado_em = db.Column(db.DateTime, default=datetime.now)
    revogada_em = db.Column(db.DateTime, nullable=True)

    autorizado = db.relationship('Autorizado', backref=db.backref('autorizacoes', cascade='all, delete-orphan'))
    aluno = db.relationship('Aluno', backref=db.backref('autorizacoes', cascade='all, delete-orphan'))

    def valida_em(self, data):
        return self.revogada_em is None and self.data_inicio <= data <= self.data_fim

    def situacao(self, hoje=None):
        hoje = hoje or date.today()
        if self.revogada_em:
            return 'revogada'
        if hoje < self.data_inicio:
            return 'agendada'
        if hoje > self.data_fim:
            return 'encerrada'
        return 'vigente'

    @staticmethod
    def validar_periodo(data_inicio, data_fim, hoje=None):
        hoje = hoje or date.today()
        if not data_inicio or not data_fim:
            return 'Informe a data de início e a data de fim.'
        if data_inicio < hoje:
            return 'A data de início não pode estar no passado.'
        if data_fim < data_inicio:
            return 'A data de fim precisa ser igual ou posterior à data de início.'
        return None

    @staticmethod
    def converter_data(texto):
        try:
            return date.fromisoformat(texto)
        except (TypeError, ValueError):
            return None