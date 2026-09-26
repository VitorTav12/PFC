from datetime import datetime

from app.extensions import db


class Movimentacao(db.Model):
    __tablename__ = 'movimentacao'

    id = db.Column(db.Integer, primary_key=True)
    aluno_id = db.Column(db.Integer, db.ForeignKey('aluno.id'), nullable=False)
    data = db.Column(db.Date, default=lambda: datetime.now().date(), nullable=False)
    horario = db.Column(db.Time, default=lambda: datetime.now().time(), nullable=False)
    responsavel_retirou_id = db.Column(db.Integer, db.ForeignKey('responsavel.id'), nullable=True)
    autorizado_retirou_id = db.Column(db.Integer, db.ForeignKey('autorizado.id'), nullable=True)

    responsavel_retirou = db.relationship('Responsavel')
    autorizado_retirou = db.relationship('Autorizado')
