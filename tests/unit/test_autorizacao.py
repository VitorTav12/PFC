from datetime import date, datetime

import pytest

from app.models import Autorizacao

HOJE = date(2026, 11, 10)
INICIO = date(2026, 11, 10)
FIM = date(2026, 11, 20)


def nova_autorizacao(inicio=INICIO, fim=FIM, revogada_em=None):
    return Autorizacao(data_inicio=inicio, data_fim=fim, revogada_em=revogada_em)


# ---------- valida_em ----------

@pytest.mark.parametrize("dia", [
    date(2026, 11, 10),  # primeiro dia (limite inferior)
    date(2026, 11, 15),  # meio do período
    date(2026, 11, 20),  # último dia (limite superior)
])
def test_validaEm_dentroDoPeriodoInclusiveLimites_deveRetornarTrue(dia):
    assert nova_autorizacao().valida_em(dia) is True


@pytest.mark.parametrize("dia", [date(2026, 11, 9), date(2026, 11, 21)])
def test_validaEm_foraDoPeriodo_deveRetornarFalse(dia):
    assert nova_autorizacao().valida_em(dia) is False


def test_validaEm_autorizacaoRevogada_deveRetornarFalseMesmoDentroDoPeriodo():
    autorizacao = nova_autorizacao(revogada_em=datetime(2026, 11, 11, 9, 0))
    assert autorizacao.valida_em(date(2026, 11, 15)) is False


# ---------- situacao ----------

def test_situacao_antesDoInicio_deveSerAgendada():
    assert nova_autorizacao().situacao(hoje=date(2026, 11, 9)) == "agendada"


@pytest.mark.parametrize("hoje", [date(2026, 11, 10), date(2026, 11, 15), date(2026, 11, 20)])
def test_situacao_dentroDoPeriodo_deveSerVigente(hoje):
    assert nova_autorizacao().situacao(hoje=hoje) == "vigente"


def test_situacao_aposOFim_deveSerEncerrada():
    assert nova_autorizacao().situacao(hoje=date(2026, 11, 21)) == "encerrada"


def test_situacao_revogada_deveTerPrioridadeSobreAsDemais():
    autorizacao = nova_autorizacao(revogada_em=datetime(2026, 11, 11))
    assert autorizacao.situacao(hoje=date(2026, 11, 15)) == "revogada"
    assert autorizacao.situacao(hoje=date(2026, 12, 31)) == "revogada"


# ---------- validar_periodo ----------

def test_validarPeriodo_comPeriodoValido_deveRetornarNone():
    assert Autorizacao.validar_periodo(date(2026, 11, 11), date(2026, 11, 15), hoje=HOJE) is None


def test_validarPeriodo_comInicioIgualAHoje_deveAceitar():
    assert Autorizacao.validar_periodo(HOJE, date(2026, 11, 15), hoje=HOJE) is None


def test_validarPeriodo_comInicioIgualAoFim_deveAceitarPeriodoDeUmDia():
    assert Autorizacao.validar_periodo(date(2026, 11, 12), date(2026, 11, 12), hoje=HOJE) is None


@pytest.mark.parametrize("inicio, fim", [(None, FIM), (INICIO, None), (None, None)])
def test_validarPeriodo_comDataAusente_deveExigirAsDuasDatas(inicio, fim):
    erro = Autorizacao.validar_periodo(inicio, fim, hoje=HOJE)
    assert erro == "Informe a data de início e a data de fim."


def test_validarPeriodo_comInicioNoPassado_deveRejeitar():
    erro = Autorizacao.validar_periodo(date(2026, 11, 9), date(2026, 11, 15), hoje=HOJE)
    assert erro == "A data de início não pode estar no passado."


def test_validarPeriodo_comFimAnteriorAoInicio_deveRejeitar():
    erro = Autorizacao.validar_periodo(date(2026, 11, 15), date(2026, 11, 12), hoje=HOJE)
    assert erro == "A data de fim precisa ser igual ou posterior à data de início."


# ---------- converter_data ----------

def test_converterData_comFormatoIso_deveRetornarDate():
    assert Autorizacao.converter_data("2026-11-10") == date(2026, 11, 10)


@pytest.mark.parametrize("texto", ["10/11/2026", "2026-13-40", "texto", "", None, 20261110])
def test_converterData_comEntradaInvalida_deveRetornarNone(texto):
    assert Autorizacao.converter_data(texto) is None
