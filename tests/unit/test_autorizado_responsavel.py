from types import SimpleNamespace

import pytest

from app.models import Autorizado, Responsavel


def arquivo(nome):
    return SimpleNamespace(filename=nome)


@pytest.mark.parametrize("nome", ["foto.png", "foto.jpg", "foto.jpeg", "FOTO.JPG", "minha.foto.PnG"])
def test_fotoValida_comExtensaoPermitida_deveRetornarTrue(nome):
    assert Autorizado.foto_valida(arquivo(nome)) is True


@pytest.mark.parametrize("nome", ["foto.gif", "foto.pdf", "foto.jpg.exe", "foto.svg", "foto"])
def test_fotoValida_comExtensaoNaoPermitidaOuSemExtensao_deveRetornarFalse(nome):
    assert Autorizado.foto_valida(arquivo(nome)) is False


@pytest.mark.parametrize("entrada", [None, arquivo(""), arquivo(None)])
def test_fotoValida_semArquivoOuSemNome_deveRetornarFalse(entrada):
    assert Autorizado.foto_valida(entrada) is False


def test_apagarFoto_semNomeDeArquivo_naoDeveFazerNada():
    assert Autorizado.apagar_foto(None) is None
    assert Autorizado.apagar_foto("") is None


def test_criarResponsavel_comEmailSujo_deveNormalizarAoAtribuir():
    responsavel = Responsavel(nome="Ana", email_pessoal="  ANA@Mail.COM ")
    assert responsavel.email_pessoal == "ana@mail.com"
