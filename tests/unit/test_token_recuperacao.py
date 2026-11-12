from datetime import datetime, timedelta

from app.models import TokenRecuperacao


def novo_token(expira_em=None, usado_em=None):
    return TokenRecuperacao(
        usuario_id=1,
        token_hash="x" * 64,
        expira_em=expira_em or datetime.now() + timedelta(minutes=30),
        usado_em=usado_em,
    )


def test_calcularHash_deveRetornarSha256EmHexadecimal():
    resultado = TokenRecuperacao.calcular_hash("abc")
    assert resultado == "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"
    assert len(resultado) == 64


def test_calcularHash_deveSerDeterministico():
    assert TokenRecuperacao.calcular_hash("token-1") == TokenRecuperacao.calcular_hash("token-1")


def test_calcularHash_comTokensDiferentes_deveGerarHashesDiferentes():
    assert TokenRecuperacao.calcular_hash("token-1") != TokenRecuperacao.calcular_hash("token-2")


def test_calcularHash_naoDeveExporOTokenOriginal():
    assert "segredo" not in TokenRecuperacao.calcular_hash("segredo")


def test_valido_tokenRecemCriado_deveRetornarTrue():
    assert novo_token().valido() is True


def test_valido_tokenExpirado_deveRetornarFalse():
    assert novo_token(expira_em=datetime.now() - timedelta(seconds=1)).valido() is False


def test_valido_tokenJaUsado_deveRetornarFalse():
    assert novo_token(usado_em=datetime.now()).valido() is False
