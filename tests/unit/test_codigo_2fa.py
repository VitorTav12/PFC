from datetime import datetime, timedelta

import pytest

from app.models import Codigo2FA
from app.models.codigo_2fa import MAX_TENTATIVAS


@pytest.fixture(autouse=True)
def hash_sem_flask(monkeypatch):
    """calcular_hash usa current_app.config; no teste unitário trocamos por um hash fake."""
    monkeypatch.setattr(Codigo2FA, "calcular_hash", staticmethod(lambda codigo: f"h-{codigo}"))


def novo_codigo(codigo="123456", expira_em=None, usado_em=None, tentativas=0, criado_em=None):
    agora = datetime.now()
    return Codigo2FA(
        usuario_id=1,
        codigo_hash=f"h-{codigo}",
        expira_em=expira_em or agora + timedelta(minutes=10),
        usado_em=usado_em,
        tentativas=tentativas,
        criado_em=criado_em or agora,
    )


# ---------- valido ----------

def test_valido_codigoRecemCriado_deveRetornarTrue():
    assert novo_codigo().valido() is True


def test_valido_codigoExpirado_deveRetornarFalse():
    codigo = novo_codigo(expira_em=datetime.now() - timedelta(seconds=1))
    assert codigo.valido() is False


def test_valido_codigoJaUsado_deveRetornarFalse():
    assert novo_codigo(usado_em=datetime.now()).valido() is False


def test_valido_comTentativasNoLimiteMenosUm_deveRetornarTrue():
    assert novo_codigo(tentativas=MAX_TENTATIVAS - 1).valido() is True


def test_valido_comTentativasNoLimite_deveRetornarFalse():
    assert novo_codigo(tentativas=MAX_TENTATIVAS).valido() is False


# ---------- pode_reenviar ----------

def test_podeReenviar_codigoCriadoAgora_deveRetornarFalse():
    assert novo_codigo().pode_reenviar() is False


def test_podeReenviar_aposIntervaloMinimo_deveRetornarTrue():
    assert novo_codigo(criado_em=datetime.now() - timedelta(seconds=61)).pode_reenviar() is True


def test_podeReenviar_poucosSegundosAntesDoIntervalo_deveRetornarFalse():
    assert novo_codigo(criado_em=datetime.now() - timedelta(seconds=30)).pode_reenviar() is False


# ---------- conferir ----------

def test_conferir_comCodigoCorreto_deveRetornarTrueEMarcarComoUsado():
    codigo = novo_codigo("654321")
    assert codigo.conferir("654321") is True
    assert codigo.usado_em is not None
    assert codigo.valido() is False  # uso único


def test_conferir_comCodigoErrado_deveRetornarFalseEIncrementarTentativas():
    codigo = novo_codigo("654321")
    assert codigo.conferir("000000") is False
    assert codigo.tentativas == 1
    assert codigo.usado_em is None
    assert codigo.valido() is True


def test_conferir_noUltimoErroPermitido_deveInvalidarOCodigo():
    codigo = novo_codigo("654321", tentativas=MAX_TENTATIVAS - 1)
    assert codigo.conferir("000000") is False
    assert codigo.tentativas == MAX_TENTATIVAS
    assert codigo.usado_em is not None
    assert codigo.valido() is False


def test_conferir_aposVariosErros_codigoCorretoAindaFunciona():
    codigo = novo_codigo("654321")
    for _ in range(MAX_TENTATIVAS - 1):
        assert codigo.conferir("000000") is False
    assert codigo.conferir("654321") is True
