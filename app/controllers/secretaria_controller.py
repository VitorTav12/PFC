from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user

from app.extensions import db
from app.models import Usuario, Responsavel, Aluno, AuditoriaLog
from app.controllers.permissoes import perfil_requerido

secretaria_bp = Blueprint('secretaria', __name__, url_prefix='/secretaria')


@secretaria_bp.route('/')
@login_required
@perfil_requerido('secretaria', 'diretoria')
def painel():
    termo_busca = request.args.get('busca', '')

    if termo_busca:
        alunos = Aluno.query.filter(Aluno.nome.ilike(f'%{termo_busca}%')).all()
    else:
        alunos = Aluno.query.all()

    return render_template('secretaria.html', alunos=alunos, termo_busca=termo_busca)


@secretaria_bp.route('/responsaveis/novo')
@login_required
@perfil_requerido('secretaria', 'diretoria')
def tela_cadastro_responsavel():
    return render_template('pais_cadastro.html')


@secretaria_bp.route('/responsaveis/novo', methods=['POST'])
@login_required
@perfil_requerido('secretaria', 'diretoria')
def cadastrar_responsavel():
    nome = (request.form.get('nome') or '').strip()
    email = (request.form.get('email') or '').strip()
    senha = request.form.get('senha') or ''

    if not nome or not email or not senha:
        flash('Preencha nome, e-mail e senha.', 'warning')
        return redirect(url_for('secretaria.tela_cadastro_responsavel'))

    if Usuario.query.filter_by(email=email).first():
        flash('Erro: Este e-mail já está cadastrado no sistema!', 'warning')
        return redirect(url_for('secretaria.tela_cadastro_responsavel'))

    try:
        novo_usuario = Usuario(
            nome=nome,
            email=email,
            nivel_acesso='pais',
            precisa_trocar_senha=True
        )
        novo_usuario.set_senha(senha)
        db.session.add(novo_usuario)
        db.session.flush()

        novo_responsavel = Responsavel(
            usuario_id=novo_usuario.id,
            nome=nome,
            email_pessoal=email
        )
        db.session.add(novo_responsavel)

        AuditoriaLog.registrar(
            usuario_id=current_user.id,
            acao='CADASTRO_RESPONSAVEL',
            detalhes=f"Cadastrou o responsável '{nome}'"
        )
        db.session.commit()

        flash(f'Responsável {nome} cadastrado com sucesso! No primeiro acesso ele deverá trocar a senha e aceitar os termos.', 'success')
        return redirect(url_for('secretaria.painel'))

    except Exception:
        db.session.rollback()
        flash('Erro ao realizar o cadastro. Tente novamente.', 'danger')
        return redirect(url_for('secretaria.tela_cadastro_responsavel'))


@secretaria_bp.route('/alunos/novo', methods=['GET', 'POST'])
@login_required
@perfil_requerido('secretaria', 'diretoria')
def cadastrar_aluno():
    responsaveis = Responsavel.query.all()

    if request.method == 'POST':
        nome = (request.form.get('nome') or '').strip()
        turma = (request.form.get('turma') or '').strip()
        numero_matricula = (request.form.get('numero_matricula') or '').strip()
        responsavel_id = request.form.get('responsavel_id', type=int)

        if not nome or not turma or not numero_matricula or not responsavel_id:
            flash('Preencha todos os campos.', 'warning')
            return render_template('aluno_cadastro.html', responsaveis=responsaveis)

        if not Responsavel.query.get(responsavel_id):
            flash('Responsável não encontrado.', 'warning')
            return render_template('aluno_cadastro.html', responsaveis=responsaveis)

        if Aluno.query.filter_by(numero_matricula=numero_matricula).first():
            flash('Já existe um aluno com essa matrícula.', 'warning')
            return render_template('aluno_cadastro.html', responsaveis=responsaveis)

        novo_aluno = Aluno(
            nome=nome,
            turma=turma,
            numero_matricula=numero_matricula,
            responsavel_id=responsavel_id
        )
        db.session.add(novo_aluno)

        AuditoriaLog.registrar(
            usuario_id=current_user.id,
            acao='CADASTRO_ALUNO',
            detalhes=f"Cadastrou o aluno '{nome}' (matrícula {numero_matricula})"
        )
        db.session.commit()

        flash(f'Aluno {nome} cadastrado com sucesso!', 'success')
        return redirect(url_for('secretaria.painel'))

    return render_template('aluno_cadastro.html', responsaveis=responsaveis)
