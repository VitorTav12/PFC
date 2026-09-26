from datetime import datetime

from app.extensions import db


class Aluno(db.Model):
    __tablename__ = 'aluno'

    id = db.Column(db.Integer, primary_key=True)
    responsavel_id = db.Column(db.Integer, db.ForeignKey('responsavel.id'), nullable=False)
    nome = db.Column(db.String(150), nullable=False)
    turma = db.Column(db.String(50), nullable=False)
    numero_matricula = db.Column(db.String(50), unique=True, nullable=False)
    criado_em = db.Column(db.DateTime, default=datetime.now)

    movimentacoes = db.relationship('Movimentacao', backref='aluno')
