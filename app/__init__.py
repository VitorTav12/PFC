import os

from flask import Flask, flash, redirect, request, url_for
from flask_wtf.csrf import CSRFError

from config import Config
from app.extensions import db, login_manager, csrf


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    if not app.config.get('SECRET_KEY'):
        raise RuntimeError('SECRET_KEY não definida. Confiram o arquivo .env')

    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    db.init_app(app)
    csrf.init_app(app)

    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = "Por favor, faça login para acessar esta página."
    login_manager.login_message_category = "warning"

    from app import models  

    from app.controllers.auth_controller import auth_bp
    from app.controllers.responsavel_controller import responsavel_bp
    from app.controllers.secretaria_controller import secretaria_bp
    from app.controllers.lgpd_controller import lgpd_bp
    from app.controllers.diretoria_controller import diretoria_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(responsavel_bp)
    app.register_blueprint(secretaria_bp)
    app.register_blueprint(lgpd_bp)
    app.register_blueprint(diretoria_bp)

    from app.comandos import registrar_comandos
    registrar_comandos(app)

    @app.errorhandler(CSRFError)
    def erro_csrf(e):
        flash('Sua sessão expirou. Tente novamente.', 'warning')
        return redirect(request.referrer or url_for('auth.login'))

    @app.errorhandler(413)
    def arquivo_grande(e):
        flash('Arquivo muito grande. O limite é 5 MB.', 'warning')
        return redirect(request.referrer or url_for('auth.login'))

    @app.context_processor
    def dados_da_escola():
        return {'nome_escola': app.config['NOME_ESCOLA']}

    return app
