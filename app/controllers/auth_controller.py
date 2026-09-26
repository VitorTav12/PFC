from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from sqlalchemy import text

from app.extensions import db
from app.models import Usuario, AuditoriaLog

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
