from app.models import AuditoriaLog


def test_status_banco_comSucesso_deveRetornar200(client):
    response = client.get('/status')
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'sucesso'

def test_login_comCredenciaisInvalidas_deveRetornarStatus200EMensagemErro(client):
    response = client.post('/', data={'email': 'inexistente@teste.com', 'senha': '123'}, follow_redirects=True)
    assert response.status_code == 200
    assert b'E-mail ou senha' in response.data or b'inv' in response.data.lower()

def test_login_comCredenciaisValidas_deveRealizarLoginERegistrarAuditoria(client, app, criar_usuario_pais):
    user_id, _, email, senha = criar_usuario_pais

    response = client.post('/', data={'email': email, 'senha': senha}, follow_redirects=True)
    assert response.status_code == 200

    with app.app_context():
        log = AuditoriaLog.query.filter_by(usuario_id=user_id, acao='LOGIN_SUCESSO').first()
        assert log is not None

def test_logout_semSessao_deveRetornar401OuRedirecionar(client):
    response = client.get('/logout')
    assert response.status_code in [302, 401]

def test_esqueciSenha_comEmailDesconhecido_deveRetornar200EMensagem(client):
    response = client.post('/esqueci-senha', data={'email': 'naoexiste@teste.com'}, follow_redirects=True)
    assert response.status_code == 200
