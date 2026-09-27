from datetime import datetime

from app.extensions import db

VERSAO_TERMOS = '1.0'


class AceiteTermo(db.Model):
    __tablename__ = 'aceite_termo'

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    versao = db.Column(db.String(20), nullable=False)
    aceito_em = db.Column(db.DateTime, default=datetime.now)