from datetime import datetime

from app.extensions import db


class Responsavel(db.Model):
    __tablename__ = 'responsavel'

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), unique=True, nullable=False)
    nome = db.Column(db.String(150), nullable=False)
    email_pessoal = db.Column(db.String(255), nullable=False)
    criado_em = db.Column(db.DateTime, default=datetime.now)

    alunos = db.relationship('Aluno', backref='responsavel')
    autorizados = db.relationship('Autorizado', backref='responsavel', cascade="all, delete-orphan")
