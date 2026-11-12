import pytest

from app.models import AceiteTermo, Usuario
from app.models.aceite_termo import VERSAO_TERMOS


def novo_usuario(nivel="pais", precisa_trocar_senha=False, email="maria@escola.com"):
    return Usuario(nome="Maria", email=email, nivel_acesso=nivel,
                   precisa_trocar_senha=precisa_trocar_senha)


# ---------- normalização de e-mail ----------

@pytest.mark.parametrize("entrada, esperado", [
    ("MARIA@Escola.com", "maria@escola.com"),
    ("  maria@escola.com  ", "maria@escola.com"),
    ("\tMaria@ESCOLA.com\n", "maria@escola.com"),
    ("", ""),
    (None, ""),
])
def test_normalizarEmail_comEntradasVariadas_deveRetornarMinusculoSemEspacos(entrada, esperado):
    assert Usuario.normalizar_email(entrada) == esperado


def test_criarUsuario_comEmailSujo_deveNormalizarAoAtribuir():
    assert novo_usuario(email="  JOAO@Escola.COM ").email == "joao@escola.com"


# ---------- validação de nova senha ----------

def test_validarNovaSenha_comSenhaValida_deveRetornarNone():
    assert Usuario.validar_nova_senha("abc12345", "abc12345") is None


def test_validarNovaSenha_comOitoCaracteres_deveAceitarLimiteInferior():
    assert Usuario.validar_nova_senha("abcdef12", "abcdef12") is None


def test_validarNovaSenha_comSeteCaracteres_deveRejeitarPorTamanho():
    erro = Usuario.validar_nova_senha("abcde12", "abcde12")
    assert erro == "A nova senha deve ter pelo menos 8 caracteres."


def test_validarNovaSenha_comSomenteLetras_deveExigirNumeros():
    erro = Usuario.validar_nova_senha("abcdefgh", "abcdefgh")
    assert erro == "A nova senha deve ter letras e números."


def test_validarNovaSenha_comSomenteNumeros_deveExigirLetras():
    erro = Usuario.validar_nova_senha("12345678", "12345678")
    assert erro == "A nova senha deve ter letras e números."


def test_validarNovaSenha_comConfirmacaoDiferente_deveRejeitar():
    erro = Usuario.validar_nova_senha("abc12345", "abc12346")
    assert erro == "A confirmação não é igual à nova senha."


def test_validarNovaSenha_comSenhaVazia_deveRejeitarPorTamanho():
    assert "pelo menos 8" in Usuario.validar_nova_senha("", "")


# ---------- senha (hash) ----------

def test_setSenha_deveGuardarHashENaoOTextoPuro():
    usuario = novo_usuario()
    usuario.set_senha("Senha123!")
    assert usuario.senha != "Senha123!"
    assert "Senha123!" not in usuario.senha


def test_checarSenha_comSenhaCorreta_deveRetornarTrue():
    usuario = novo_usuario()
    usuario.set_senha("Senha123!")
    assert usuario.checar_senha("Senha123!") is True


def test_checarSenha_comSenhaErrada_deveRetornarFalse():
    usuario = novo_usuario()
    usuario.set_senha("Senha123!")
    assert usuario.checar_senha("senha123!") is False


def test_checarSenha_semSenhaDefinida_deveRetornarFalse():
    usuario = novo_usuario()
    usuario.senha = None
    assert usuario.checar_senha("qualquer") is False


def test_checarSenha_comHashInvalido_deveRetornarFalseSemLancarErro():
    usuario = novo_usuario()
    usuario.senha = "isto-nao-e-um-hash"
    assert usuario.checar_senha("qualquer") is False


# ---------- 2FA por perfil ----------

@pytest.mark.parametrize("nivel, esperado", [
    ("secretaria", True),
    ("diretoria", True),
    ("pais", False),
    ("desconhecido", False),
])
def test_exige2fa_porNivelDeAcesso_deveExigirSomenteParaEquipeInterna(nivel, esperado):
    assert novo_usuario(nivel=nivel).exige_2fa() is esperado


def test_emailMascarado_deveManterDoisPrimeirosCaracteresEODominio():
    assert novo_usuario(email="maria.silva@escola.com").email_mascarado() == "XX***@escola.com"


def test_emailMascarado_comNomeCurto_deveFuncionarSemErro():
    assert novo_usuario(email="a@escola.com").email_mascarado() == "a***@escola.com"


# ---------- termos de uso e primeiro acesso ----------

def test_aceitouTermosAtuais_semNenhumAceite_deveRetornarFalse():
    assert novo_usuario().aceitou_termos_atuais() is False


def test_aceitouTermosAtuais_comVersaoAntiga_deveRetornarFalse():
    usuario = novo_usuario()
    usuario.aceites = [AceiteTermo(versao="0.9")]
    assert usuario.aceitou_termos_atuais() is False


def test_aceitouTermosAtuais_comVersaoAtual_deveRetornarTrue():
    usuario = novo_usuario()
    usuario.aceites = [AceiteTermo(versao="0.9"), AceiteTermo(versao=VERSAO_TERMOS)]
    assert usuario.aceitou_termos_atuais() is True


def test_pendentePrimeiroAcesso_paisComSenhaTemporaria_deveRetornarTrue():
    usuario = novo_usuario(precisa_trocar_senha=True)
    usuario.aceites = [AceiteTermo(versao=VERSAO_TERMOS)]
    assert usuario.pendente_primeiro_acesso() is True


def test_pendentePrimeiroAcesso_paisSemAceiteDosTermos_deveRetornarTrue():
    assert novo_usuario(precisa_trocar_senha=False).pendente_primeiro_acesso() is True


def test_pendentePrimeiroAcesso_paisComTudoEmDia_deveRetornarFalse():
    usuario = novo_usuario(precisa_trocar_senha=False)
    usuario.aceites = [AceiteTermo(versao=VERSAO_TERMOS)]
    assert usuario.pendente_primeiro_acesso() is False


@pytest.mark.parametrize("nivel", ["secretaria", "diretoria"])
def test_pendentePrimeiroAcesso_perfilInterno_nuncaDeveSerPendente(nivel):
    usuario = novo_usuario(nivel=nivel, precisa_trocar_senha=True)
    assert usuario.pendente_primeiro_acesso() is False
