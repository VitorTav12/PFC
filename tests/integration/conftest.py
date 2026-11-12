from unittest.mock import patch

import pytest
from sqlalchemy.pool import StaticPool

from app import create_app, db
from app.models import Usuario, Responsavel, AceiteTermo
from app.models.aceite_termo import VERSAO_TERMOS

@pytest.fixture(scope='session')
def app():
    app = create_app()
    app.config.update({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "SQLALCHEMY_ENGINE_OPTIONS": {
            "poolclass": StaticPool,
            "connect_args": {"check_same_thread": False}
        },
        "WTF_CSRF_ENABLED": False,
        "SERVER_NAME": "localhost.localdomain",
        "UPLOAD_FOLDER": "/tmp"
    })
    
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture(autouse=True)
def mock_brevo():
    with patch('app.models.EmailBrevo.enviar', return_value='sucesso'):
        yield

@pytest.fixture
def criar_usuario_pais(app):
    with app.app_context():
        import time
        ts = str(time.time_ns())
        
        user = Usuario(
            nome=f"Pai Teste {ts}",
            email=f"pai_{ts}@teste.com",
            nivel_acesso="pais",
            precisa_trocar_senha=False
        )
        user.set_senha("Senha123!")
        db.session.add(user)
        db.session.flush()
        
        aceite = AceiteTermo(usuario_id=user.id, versao=VERSAO_TERMOS)
        db.session.add(aceite)
        
        resp = Responsavel(usuario_id=user.id, nome=user.nome, email_pessoal=user.email)
        db.session.add(resp)
        db.session.commit()
        return user.id, resp.id, user.email, "Senha123!"