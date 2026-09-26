import os
import uuid
from datetime import datetime

from flask import current_app

from app.extensions import db

EXTENSOES_FOTO = {'png', 'jpg', 'jpeg'}


class Autorizado(db.Model):
    __tablename__ = 'autorizado'

    id = db.Column(db.Integer, primary_key=True)
    responsavel_id = db.Column(db.Integer, db.ForeignKey('responsavel.id'), nullable=False)
    nome = db.Column(db.String(150), nullable=False)
    grau_parentesco = db.Column(db.String(50), nullable=False)
    foto = db.Column(db.Text, nullable=False)  
    criado_em = db.Column(db.DateTime, default=datetime.now)

    @staticmethod
    def foto_valida(arquivo):
        if not arquivo or not arquivo.filename or '.' not in arquivo.filename:
            return False
        return arquivo.filename.rsplit('.', 1)[1].lower() in EXTENSOES_FOTO

    @staticmethod
    def salvar_foto(arquivo):
        extensao = arquivo.filename.rsplit('.', 1)[1].lower()
        nome_arquivo = f'{uuid.uuid4().hex}.{extensao}'
        arquivo.save(os.path.join(current_app.config['UPLOAD_FOLDER'], nome_arquivo))
        return nome_arquivo

    @staticmethod
    def apagar_foto(nome_arquivo):
        if not nome_arquivo:
            return
        caminho = os.path.join(current_app.config['UPLOAD_FOLDER'], nome_arquivo)
        if os.path.exists(caminho):
            os.remove(caminho)
