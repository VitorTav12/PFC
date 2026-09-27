from datetime import datetime

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from sqlalchemy import text

from app.extensions import db
from app.models import Usuario, AuditoriaLog, TokenRecuperacao, EmailBrevo
from app.models.token_recuperacao import VALIDADE_TOKEN

auth_bp = Blueprint('auth', __name__)


def pagina_inicial(usuario):
    if usuario.nivel_acesso in ['diretoria', 'secretaria']:
        return url_for('secretaria.painel')
    if usuario.nivel_acesso == 'pais':
        return url_for('responsavel.painel')
    return None


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

        usuario = Usuario.query.filter_by(email=email_input).first()

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

        destino = pagina_inicial(usuario)
        if not destino:
            flash('Perfil de acesso sem página definida. Procure a secretaria.', 'danger')
            return render_template('login.html')

        login_user(usuario, remember=bool(request.form.get('remember')))

        AuditoriaLog.registrar(
            usuario_id=usuario.id,
            acao='LOGIN_SUCESSO',
            detalhes=f"Usuário '{usuario.nome}' ({usuario.nivel_acesso}) realizou login."
        )
        db.session.commit()

        flash(f'Bem-vindo(a), {usuario.nome}!', 'success')
        return redirect(destino)

    return render_template('login.html')


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
        email = (request.form.get('email') or '').strip()
        usuario = Usuario.query.filter_by(email=email).first() if email else None

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
                f"Para criar uma nova senha no Portal de Controle de Saída, acesse o link abaixo "
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