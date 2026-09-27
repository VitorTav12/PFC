from datetime import datetime

from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app
from flask_login import login_user, logout_user, login_required, current_user
from sqlalchemy import text

from app.extensions import db
from app.models import Usuario, AuditoriaLog, TokenRecuperacao, EmailBrevo, Codigo2FA
from app.models.token_recuperacao import VALIDADE_TOKEN
from app.models.codigo_2fa import VALIDADE_CODIGO, MAX_TENTATIVAS

auth_bp = Blueprint('auth', __name__)

def pagina_inicial(usuario):
    if usuario.nivel_acesso == 'diretoria':
        return url_for('diretoria.painel')
    if usuario.nivel_acesso == 'secretaria':
        return url_for('secretaria.painel')
    if usuario.nivel_acesso == 'pais':
        return url_for('responsavel.painel')
    return None


def enviar_codigo_2fa(usuario):
    codigo = Codigo2FA.gerar(usuario.id)
    AuditoriaLog.registrar(
        usuario_id=usuario.id,
        acao='2FA_CODIGO_ENVIADO',
        detalhes=f"Código de verificação gerado para '{usuario.nome}'."
    )
    db.session.commit()

    minutos = int(VALIDADE_CODIGO.total_seconds() // 60)
    html = render_template('emails/codigo_2fa.html', nome=usuario.nome, codigo=codigo, minutos=minutos)
    texto = (
        f"Olá, {usuario.nome}.\n\n"
        f"Seu código de acesso ao portal da {current_app.config['NOME_ESCOLA']} é: {codigo}\n"
        f"Ele vale por {minutos} minutos e só pode ser usado uma vez.\n\n"
        "Se não foi você que tentou entrar, troque sua senha e avise a direção da escola."
    )

    resultado = EmailBrevo.enviar(usuario.email, usuario.nome, 'Seu código de acesso', html, texto)
    if resultado == 'falhou':
        AuditoriaLog.registrar(
            usuario_id=usuario.id,
            acao='2FA_EMAIL_FALHOU',
            detalhes="Não foi possível enviar o código de verificação pela API externa."
        )
        db.session.commit()
    return resultado


def finalizar_login(usuario, lembrar):
    login_user(usuario, remember=lembrar)

    AuditoriaLog.registrar(
        usuario_id=usuario.id,
        acao='LOGIN_SUCESSO',
        detalhes=f"Usuário '{usuario.nome}' ({usuario.nivel_acesso}) realizou login."
    )
    db.session.commit()

    flash(f'Bem-vindo(a), {usuario.nome}!', 'success')
    return redirect(pagina_inicial(usuario))


def limpar_2fa_pendente():
    session.pop('2fa_usuario_id', None)
    session.pop('2fa_lembrar', None)


@auth_bp.route('/status')
def status_banco():
    try:
        db.session.execute(text('SELECT 1'))
        return {"status": "sucesso", "mensagem": "Conexão com PostgreSQL ativa e respondendo!"}, 200
    except Exception:
        return {"status": "erro", "mensagem": "Banco de dados indisponível."}, 500


@auth_bp.route('/', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated and pagina_inicial(current_user):
        return redirect(pagina_inicial(current_user))

    if request.method == 'POST':
        email_input = request.form.get('email')
        senha_input = request.form.get('senha')

        usuario = Usuario.buscar_por_email(email_input)

        if not usuario or not usuario.checar_senha(senha_input):
            if usuario:
                AuditoriaLog.registrar(
                    usuario_id=usuario.id,
                    acao='LOGIN_FALHA',
                    detalhes=f"Tentativa de login com senha incorreta para '{usuario.nome}'."
                )
            else:
                AuditoriaLog.registrar(
                    usuario_id=None,
                    acao='LOGIN_FALHA',
                    detalhes="Tentativa de login com e-mail não cadastrado."
                )
            db.session.commit()

            flash('E-mail ou senha inválidos!', 'danger')
            return render_template('login.html')

        if not pagina_inicial(usuario):
            flash('Perfil de acesso sem página definida. Procure a secretaria.', 'danger')
            return render_template('login.html')

        lembrar = bool(request.form.get('remember'))

        if usuario.exige_2fa():
            enviar_codigo_2fa(usuario)
            session['2fa_usuario_id'] = usuario.id
            session['2fa_lembrar'] = lembrar
            return redirect(url_for('auth.verificar_codigo'))

        return finalizar_login(usuario, lembrar)

    return render_template('login.html')


@auth_bp.route('/verificar-codigo', methods=['GET', 'POST'])
def verificar_codigo():
    usuario_id = session.get('2fa_usuario_id')
    usuario = Usuario.query.get(usuario_id) if usuario_id else None

    if not usuario:
        flash('Faça login novamente.', 'warning')
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        codigo = Codigo2FA.atual(usuario.id)
        digitado = (request.form.get('codigo') or '').strip()

        if not codigo or not codigo.valido():
            limpar_2fa_pendente()
            flash('O código expirou. Faça login novamente para receber outro.', 'warning')
            return redirect(url_for('auth.login'))

        if codigo.conferir(digitado):
            AuditoriaLog.registrar(
                usuario_id=usuario.id,
                acao='2FA_VALIDADO',
                detalhes=f"Usuário '{usuario.nome}' confirmou o código de verificação."
            )
            lembrar = session.get('2fa_lembrar', False)
            limpar_2fa_pendente()
            return finalizar_login(usuario, lembrar)

        AuditoriaLog.registrar(
            usuario_id=usuario.id,
            acao='2FA_FALHA',
            detalhes=f"Código de verificação incorreto ({codigo.tentativas}/{MAX_TENTATIVAS})."
        )
        db.session.commit()

        if not codigo.valido():
            limpar_2fa_pendente()
            flash('Muitas tentativas erradas. Faça login novamente para receber outro código.', 'danger')
            return redirect(url_for('auth.login'))

        flash('Código incorreto. Confira o e-mail e tente de novo.', 'danger')

    return render_template('verificar_codigo.html', email=usuario.email_mascarado())


@auth_bp.route('/verificar-codigo/reenviar', methods=['POST'])
def reenviar_codigo():
    usuario_id = session.get('2fa_usuario_id')
    usuario = Usuario.query.get(usuario_id) if usuario_id else None

    if not usuario:
        return redirect(url_for('auth.login'))

    codigo = Codigo2FA.atual(usuario.id)
    if codigo and not codigo.pode_reenviar():
        flash('Aguarde um minuto antes de pedir outro código.', 'warning')
        return redirect(url_for('auth.verificar_codigo'))

    enviar_codigo_2fa(usuario)
    flash('Enviamos um novo código para o seu e-mail.', 'info')
    return redirect(url_for('auth.verificar_codigo'))


@auth_bp.route('/logout')
@login_required
def logout():
    AuditoriaLog.registrar(
        usuario_id=current_user.id,
        acao='LOGOUT',
        detalhes=f"Usuário '{current_user.nome}' encerrou a sessão."
    )
    db.session.commit()

    logout_user()
    flash('Sessão encerrada.', 'info')
    return redirect(url_for('auth.login'))


@auth_bp.route('/esqueci-senha', methods=['GET', 'POST'])
def esqueci_senha():
    if request.method == 'POST':
        usuario = Usuario.buscar_por_email(request.form.get('email'))

        if usuario:
            token = TokenRecuperacao.gerar(usuario)
            AuditoriaLog.registrar(
                usuario_id=usuario.id,
                acao='RECUPERACAO_SOLICITADA',
                detalhes=f"Recuperação de senha solicitada para '{usuario.nome}'."
            )
            db.session.commit()

            minutos = int(VALIDADE_TOKEN.total_seconds() // 60)
            link = url_for('auth.redefinir_senha', token=token, _external=True)
            html = render_template('emails/recuperacao_senha.html', nome=usuario.nome, link=link, minutos=minutos)
            texto = (
                f"Olá, {usuario.nome}.\n\n"
                f"Para criar uma nova senha no portal da {current_app.config['NOME_ESCOLA']}, acesse o link abaixo "
                f"(válido por {minutos} minutos e para um único uso):\n{link}\n\n"
                "Se você não pediu a recuperação, ignore este e-mail. Sua senha atual continua valendo."
            )

            resultado = EmailBrevo.enviar(usuario.email, usuario.nome, 'Recuperação de senha', html, texto)
            if resultado == 'falhou':
                AuditoriaLog.registrar(
                    usuario_id=usuario.id,
                    acao='RECUPERACAO_EMAIL_FALHOU',
                    detalhes="Não foi possível enviar o e-mail de recuperação pela API externa."
                )
                db.session.commit()
        else:
            AuditoriaLog.registrar(
                usuario_id=None,
                acao='RECUPERACAO_EMAIL_DESCONHECIDO',
                detalhes="Recuperação de senha solicitada para e-mail não cadastrado."
            )
            db.session.commit()

        flash('Se o e-mail estiver cadastrado, você vai receber um link para criar uma nova senha.', 'info')
        return redirect(url_for('auth.login'))

    return render_template('esqueci_senha.html')


@auth_bp.route('/redefinir-senha/<token>', methods=['GET', 'POST'])
def redefinir_senha(token):
    registro = TokenRecuperacao.buscar(token)

    if not registro or not registro.valido():
        if registro:
            AuditoriaLog.registrar(
                usuario_id=registro.usuario_id,
                acao='RECUPERACAO_LINK_INVALIDO',
                detalhes="Tentativa de uso de link de recuperação expirado ou já utilizado."
            )
            db.session.commit()
        flash('Este link é inválido ou expirou. Peça um novo link de recuperação.', 'warning')
        return redirect(url_for('auth.esqueci_senha'))

    if request.method == 'POST':
        nova_senha = request.form.get('nova_senha') or ''
        confirmacao = request.form.get('confirmacao') or ''

        erro = Usuario.validar_nova_senha(nova_senha, confirmacao)
        if erro:
            flash(erro, 'warning')
            return render_template('redefinir_senha.html', token=token)

        usuario = registro.usuario
        usuario.set_senha(nova_senha)
        usuario.precisa_trocar_senha = False
        registro.usado_em = datetime.now()

        AuditoriaLog.registrar(
            usuario_id=usuario.id,
            acao='RECUPERACAO_CONCLUIDA',
            detalhes=f"Usuário '{usuario.nome}' criou uma nova senha pelo link de recuperação."
        )
        db.session.commit()

        flash('Senha alterada com sucesso! Entre com a nova senha.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('redefinir_senha.html', token=token)