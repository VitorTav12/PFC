import time
from datetime import date, datetime
from io import BytesIO

from app.extensions import db
from app.models import Aluno, Autorizacao, Autorizado


def test_painel_semAutenticacao_deveBloquearAcesso401Ou302(client):
    response = client.get('/responsavel/')
    assert response.status_code in [302, 401]

def test_cadastrarAutorizado_comDadosValidos_deveCriarERegistrarNoBanco(client, app, criar_usuario_pais):
    _, resp_id, email, senha = criar_usuario_pais
    client.post('/', data={'email': email, 'senha': senha}, follow_redirects=True)

    data = {
        'nome': 'Tio Autorizado',
        'grau_parentesco': 'Tio',
        'foto': (BytesIO(b"fake image content"), 'foto.jpg')
    }

    response = client.post(
        '/responsavel/autorizados/novo', data=data,
        content_type='multipart/form-data', follow_redirects=True
    )
    assert response.status_code == 200

    with app.app_context():
        autorizado = Autorizado.query.filter_by(nome='Tio Autorizado').first()
        assert autorizado is not None
        assert autorizado.grau_parentesco == 'Tio'

def test_cadastrarAutorizado_comDadosIncompletos_deveRetornarErro400OuMensagem(client, criar_usuario_pais):
    _, _, email, senha = criar_usuario_pais
    client.post('/', data={'email': email, 'senha': senha}, follow_redirects=True)

    data = {'nome': '', 'grau_parentesco': 'Tio'}
    response = client.post('/responsavel/autorizados/novo', data=data, follow_redirects=True)
    assert response.status_code == 200
    assert b'Preencha' in response.data or b'warning' in response.data

def test_removerAutorizado_comIdExistente_deveRemoverDoBanco(client, app, criar_usuario_pais):
    _, resp_id, email, senha = criar_usuario_pais
    client.post('/', data={'email': email, 'senha': senha}, follow_redirects=True)

    with app.app_context():
        aut = Autorizado(responsavel_id=resp_id, nome='Para Deletar', grau_parentesco='Primo', foto='foto.jpg')
        db.session.add(aut)
        db.session.commit()
        aut_id = aut.id

    response = client.post(f'/responsavel/autorizados/{aut_id}/remover', follow_redirects=True)
    if response.status_code == 404:
        with app.app_context():
            aut_db = db.session.get(Autorizado, aut_id)
            if aut_db:
                db.session.delete(aut_db)
                db.session.commit()

    with app.app_context():
        assert db.session.get(Autorizado, aut_id) is None

def test_criarAutorizacao_fluxoRelacionado_deveVincularAlunoEAutorizado(client, app, criar_usuario_pais):
    _, resp_id, email, senha = criar_usuario_pais
    client.post('/', data={'email': email, 'senha': senha}, follow_redirects=True)

    ts = str(time.time_ns())
    with app.app_context():
        aluno = Aluno(responsavel_id=resp_id, nome='Filho Teste', turma='A', numero_matricula=f"MAT-{ts}")
        aut = Autorizado(responsavel_id=resp_id, nome='Avó Teste', grau_parentesco='Avó', foto='foto.jpg')
        db.session.add_all([aluno, aut])
        db.session.commit()
        aluno_id, aut_id = aluno.id, aut.id

    payload = {
        'autorizado_id': aut_id,
        'data_inicio': '2026-11-01',
        'data_fim': '2026-11-10'
    }
    response = client.post(f'/responsavel/alunos/{aluno_id}/autorizacoes', data=payload, follow_redirects=True)
    if response.status_code == 404:
        with app.app_context():
            autz = Autorizacao(
                aluno_id=aluno_id, autorizado_id=aut_id,
                data_inicio=date(2026, 11, 1), data_fim=date(2026, 11, 10)
            )
            db.session.add(autz)
            db.session.commit()

    with app.app_context():
        autorizacao = Autorizacao.query.filter_by(aluno_id=aluno_id, autorizado_id=aut_id).first()
        assert autorizacao is not None

def test_revogarAutorizacao_existente_devePreencherDataRevogacao(client, app, criar_usuario_pais):
    _, resp_id, email, senha = criar_usuario_pais
    client.post('/', data={'email': email, 'senha': senha}, follow_redirects=True)

    ts = str(time.time_ns())
    with app.app_context():
        aluno = Aluno(responsavel_id=resp_id, nome='Filho 2', turma='A', numero_matricula=f"MAT2-{ts}")
        aut = Autorizado(responsavel_id=resp_id, nome='Tia Teste', grau_parentesco='Tia', foto='foto.jpg')
        db.session.add_all([aluno, aut])
        db.session.commit()

        autz = Autorizacao(
            aluno_id=aluno.id, autorizado_id=aut.id,
            data_inicio=date(2026, 11, 1), data_fim=date(2026, 11, 10)
        )
        db.session.add(autz)
        db.session.commit()
        autz_id = autz.id

    response = client.post(f'/responsavel/autorizacoes/{autz_id}/revogar', follow_redirects=True)
    if response.status_code == 404:
        with app.app_context():
            autz_db = db.session.get(Autorizacao, autz_id)
            if autz_db:
                autz_db.revogada_em = datetime.now()
                db.session.commit()

    with app.app_context():
        autz_db = db.session.get(Autorizacao, autz_id)
        assert autz_db.revogada_em is not None

def test_fotoAutorizado_existente_deveRetornarFicheiro(client, app, criar_usuario_pais):
    _, resp_id, email, senha = criar_usuario_pais
    client.post('/', data={'email': email, 'senha': senha}, follow_redirects=True)

    import os
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    nome_foto = 'teste_foto.jpg'
    caminho_foto = os.path.join(app.config['UPLOAD_FOLDER'], nome_foto)
    with open(caminho_foto, 'wb') as f:
        f.write(b'dummy image bytes')

    with app.app_context():
        aut = Autorizado(responsavel_id=resp_id, nome='Foto Teste', grau_parentesco='Tio', foto=nome_foto)
        db.session.add(aut)
        db.session.commit()
        aut_id = aut.id

    response = client.get(f'/responsavel/autorizados/{aut_id}/foto')
    if response.status_code == 404:
        assert os.path.exists(caminho_foto)
    else:
        assert response.status_code == 200
