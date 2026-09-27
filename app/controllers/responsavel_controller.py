from flask import Blueprint, render_template, request, redirect, url_for, flash, abort, current_app, send_from_directory
from flask_login import login_required, current_user
from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.models import Aluno, Autorizado, AuditoriaLog
from app.controllers.permissoes import perfil_requerido

responsavel_bp = Blueprint('responsavel', __name__, url_prefix='/responsavel')

@responsavel_bp.before_request
def exigir_primeiro_acesso():
    if current_user.is_authenticated and current_user.pendente_primeiro_acesso():
        return redirect(url_for('lgpd.primeiro_acesso'))

def buscar_responsavel():
    responsavel = current_user.responsavel
    if not responsavel:
        abort(403)
    return responsavel


@responsavel_bp.route('/')
@login_required
@perfil_requerido('pais')
def painel():
    responsavel = buscar_responsavel()

    alunos = Aluno.query.filter_by(responsavel_id=responsavel.id).all()
    autorizados = Autorizado.query.filter_by(responsavel_id=responsavel.id).all()

    return render_template('pais.html', responsavel=responsavel, alunos=alunos, autorizados=autorizados)


@responsavel_bp.route('/autorizados/novo', methods=['GET', 'POST'])
@login_required
@perfil_requerido('pais')
def cadastrar_autorizado():
    responsavel = buscar_responsavel()

    if request.method == 'POST':
        nome = (request.form.get('nome') or '').strip()
        grau_parentesco = (request.form.get('grau_parentesco') or '').strip()
        foto = request.files.get('foto')

        if not nome or not grau_parentesco:
            flash('Preencha o nome e o grau de parentesco.', 'warning')
            return render_template('autorizado_cadastro.html')

        if not Autorizado.foto_valida(foto):
            flash('Envie uma foto do autorizado em JPG ou PNG.', 'warning')
            return render_template('autorizado_cadastro.html')

        nome_foto = Autorizado.salvar_foto(foto)

        try:
            novo_autorizado = Autorizado(
                responsavel_id=responsavel.id,
                nome=nome,
                grau_parentesco=grau_parentesco,
                foto=nome_foto
            )
            db.session.add(novo_autorizado)
            db.session.flush()

            AuditoriaLog.registrar(
                usuario_id=current_user.id,
                acao='CADASTRO_AUTORIZADO',
                detalhes=f"Cadastrou o autorizado '{nome}' (id {novo_autorizado.id})"
            )
            db.session.commit()

        except Exception:
            db.session.rollback()
            Autorizado.apagar_foto(nome_foto)
            flash('Erro ao cadastrar o autorizado. Tente novamente.', 'danger')
            return render_template('autorizado_cadastro.html')

        flash('Autorizado cadastrado com sucesso!', 'success')
        return redirect(url_for('responsavel.painel'))

    return render_template('autorizado_cadastro.html')


@responsavel_bp.route('/autorizados/<int:id>/foto')
@login_required
@perfil_requerido('pais')
def foto_autorizado(id):
    responsavel = buscar_responsavel()

    autorizado = Autorizado.query.filter_by(id=id, responsavel_id=responsavel.id).first_or_404()
    return send_from_directory(current_app.config['UPLOAD_FOLDER'], autorizado.foto)


@responsavel_bp.route('/autorizados/<int:id>/remover', methods=['POST'])
@login_required
@perfil_requerido('pais')
def remover_autorizado(id):
    responsavel = buscar_responsavel()

    autorizado = Autorizado.query.filter_by(id=id, responsavel_id=responsavel.id).first_or_404()
    nome = autorizado.nome
    nome_foto = autorizado.foto

    try:
        db.session.delete(autorizado)
        AuditoriaLog.registrar(
            usuario_id=current_user.id,
            acao='REMOCAO_AUTORIZADO',
            detalhes=f"Removeu o autorizado '{nome}' (id {id})"
        )
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        flash('Este autorizado já tem retiradas registradas e não pode ser removido.', 'warning')
        return redirect(url_for('responsavel.painel'))

    Autorizado.apagar_foto(nome_foto)
    flash('Autorizado removido com sucesso!', 'success')
    return redirect(url_for('responsavel.painel'))
