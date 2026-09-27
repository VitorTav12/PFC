from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user

from app.extensions import db
from app.models import AceiteTermo, AuditoriaLog, Usuario
from app.models.aceite_termo import VERSAO_TERMOS
from app.controllers.permissoes import perfil_requerido

lgpd_bp = Blueprint('lgpd', __name__)


@lgpd_bp.route('/termos-de-uso')
def termos_de_uso():
    return render_template('termos_de_uso.html', versao=VERSAO_TERMOS)


@lgpd_bp.route('/politica-de-privacidade')
def politica_privacidade():
    return render_template('politica_privacidade.html', versao=VERSAO_TERMOS)


@lgpd_bp.route('/primeiro-acesso', methods=['GET', 'POST'])
@login_required
@perfil_requerido('pais')
def primeiro_acesso():
    if not current_user.pendente_primeiro_acesso():
        return redirect(url_for('responsavel.painel'))

    precisa_trocar_senha = current_user.precisa_trocar_senha
    precisa_aceitar = not current_user.aceitou_termos_atuais()

    def tela():
        return render_template(
            'primeiro_acesso.html',
            versao=VERSAO_TERMOS,
            precisa_trocar_senha=precisa_trocar_senha,
            precisa_aceitar=precisa_aceitar
        )

    if request.method == 'POST':
        if precisa_aceitar and request.form.get('aceite') != 'sim':
            flash('Para usar o portal é necessário aceitar os Termos de Uso e a Política de Privacidade.', 'warning')
            return tela()

        if precisa_trocar_senha:
            nova_senha = request.form.get('nova_senha') or ''
            confirmacao = request.form.get('confirmacao') or ''

            erro = Usuario.validar_nova_senha(nova_senha, confirmacao)
            if erro:
                flash(erro, 'warning')
                return tela()

            if current_user.checar_senha(nova_senha):
                flash('A nova senha precisa ser diferente da senha inicial.', 'warning')
                return tela()

            current_user.set_senha(nova_senha)
            current_user.precisa_trocar_senha = False
            AuditoriaLog.registrar(
                usuario_id=current_user.id,
                acao='TROCA_SENHA_INICIAL',
                detalhes=f"Usuário '{current_user.nome}' trocou a senha inicial."
            )

        if precisa_aceitar:
            db.session.add(AceiteTermo(usuario_id=current_user.id, versao=VERSAO_TERMOS))
            AuditoriaLog.registrar(
                usuario_id=current_user.id,
                acao='ACEITE_TERMOS',
                detalhes=f"Usuário '{current_user.nome}' aceitou os Termos de Uso e a Política de Privacidade (versão {VERSAO_TERMOS})."
            )

        db.session.commit()

        flash('Tudo certo! Seu acesso ao portal foi liberado.', 'success')
        return redirect(url_for('responsavel.painel'))

    return tela()