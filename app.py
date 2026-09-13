import os
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import text

app = Flask(__name__)
app.config['SECRET_KEY'] = 'chave-secreta-projeto-sccp-2026'
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = True

db = SQLAlchemy(app)

login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_message = "Por favor, faça login para acessar esta página."
login_manager.login_message_category = "warning"

class Usuario(UserMixin, db.Model):
    __tablename__ = 'usuario'

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    senha = db.Column(db.String(255), nullable=False)
    nivel_acesso = db.Column(db.String(20), nullable=False) # 'secretaria', 'diretoria', 'pais'
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)

    responsavel = db.relationship('Responsavel', backref='usuario', uselist=False, cascade="all, delete-orphan")
    logs = db.relationship('AuditoriaLog', backref='usuario')

    def set_senha(self, senha_texto_puro):
        self.senha = generate_password_hash(senha_texto_puro)

    def checar_senha(self, senha_digitada):
        if not self.senha:
            return False
        try:
            return check_password_hash(self.senha, senha_digitada)
        except Exception:
            return False

class Responsavel(db.Model):
    __tablename__ = 'responsavel'

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), unique=True, nullable=False)
    nome = db.Column(db.String(150), nullable=False)
    email_pessoal = db.Column(db.String(255), nullable=False)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)

    alunos = db.relationship('Aluno', backref='responsavel')
    autorizados = db.relationship('Autorizado', backref='responsavel', cascade="all, delete-orphan")

class Aluno(db.Model):
    __tablename__ = 'aluno'

    id = db.Column(db.Integer, primary_key=True)
    responsavel_id = db.Column(db.Integer, db.ForeignKey('responsavel.id'), nullable=False)
    nome = db.Column(db.String(150), nullable=False)
    turma = db.Column(db.String(50), nullable=False)
    numero_matricula = db.Column(db.String(50), unique=True, nullable=False)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)

    movimentacoes = db.relationship('Movimentacao', backref='aluno')

class Autorizado(db.Model):
    __tablename__ = 'autorizado'

    id = db.Column(db.Integer, primary_key=True)
    responsavel_id = db.Column(db.Integer, db.ForeignKey('responsavel.id'), nullable=False)
    nome = db.Column(db.String(150), nullable=False)
    grau_parentesco = db.Column(db.String(50), nullable=False) 
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)

class Movimentacao(db.Model):
    __tablename__ = 'movimentacao'

    id = db.Column(db.Integer, primary_key=True)
    aluno_id = db.Column(db.Integer, db.ForeignKey('aluno.id'), nullable=False)
    data = db.Column(db.Date, default=datetime.utcnow().date, nullable=False)
    horario = db.Column(db.Time, default=datetime.utcnow().time, nullable=False)
    responsavel_retirou_id = db.Column(db.Integer, db.ForeignKey('responsavel.id'), nullable=True)
    autorizado_retirou_id = db.Column(db.Integer, db.ForeignKey('autorizado.id'), nullable=True)

    responsavel_retirou = db.relationship('Responsavel')
    autorizado_retirou = db.relationship('Autorizado')

class AuditoriaLog(db.Model):
    __tablename__ = 'auditoria_log'

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    acao = db.Column(db.String(50), nullable=False)
    detalhes = db.Column(db.Text, nullable=False)
    data_horario = db.Column(db.DateTime, default=datetime.utcnow)

@login_manager.user_loader
def load_user(user_id):
    return Usuario.query.get(int(user_id))

def registrar_log(usuario_id, acao, detalhes):
    """Grava um registro na tabela auditoria_log para conformidade LGPD"""
    try:
        log = AuditoriaLog(usuario_id=usuario_id, acao=acao, detalhes=detalhes)
        db.session.add(log)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Erro ao salvar auditoria: {e}")

@app.route('/status')
def status_banco():
    try:
        db.session.execute(text('SELECT 1'))
        return {"status": "sucesso", "mensagem": "Conexão com PostgreSQL ativa e respondendo!"}, 200
    except Exception as e:
        return {"status": "erro", "mensagem": str(e)}, 500

@app.route('/', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        if current_user.nivel_acesso in ['diretoria', 'secretaria']:
            return redirect(url_for('secretaria'))
        elif current_user.nivel_acesso == 'pais':
            return redirect(url_for('pais'))

    if request.method == 'POST':
        email_input = request.form.get('email')
        senha_input = request.form.get('senha')

        usuario = Usuario.query.filter_by(email=email_input).first()

        if not usuario or not usuario.checar_senha(senha_input):
            flash('E-mail ou senha inválidos!', 'danger')
            return render_template('login.html')

        login_user(usuario)
        
        registrar_log(
            usuario_id=usuario.id,
            acao='LOGIN_SUCESSO',
            detalhes=f"Usuário '{usuario.nome}' ({usuario.nivel_acesso}) realizou login."
        )

        if usuario.nivel_acesso in ['diretoria', 'secretaria']:
            flash(f'Bem-vindo(a), {usuario.nome}!', 'success')
            return redirect(url_for('secretaria'))
        elif usuario.nivel_acesso == 'pais':
            flash(f'Bem-vindo(a), {usuario.nome}!', 'success')
            return redirect(url_for('pais'))

    return render_template('login.html')

@app.route('/pais')
@login_required
def pais():
    if current_user.nivel_acesso != 'pais':
        flash('Acesso não autorizado.', 'danger')
        return redirect(url_for('login'))

    responsavel = Responsavel.query.filter_by(usuario_id=current_user.id).first()
    if not responsavel:
        flash('Perfil de responsável não encontrado.', 'danger')
        return redirect(url_for('login'))

    alunos = Aluno.query.filter_by(responsavel_id=responsavel.id).all()
    
    autorizados = Autorizado.query.filter_by(responsavel_id=responsavel.id).all()

    return render_template('pais.html', responsavel=responsavel, alunos=alunos, autorizados=autorizados)

@app.route('/pais/autorizado/cadastrar', methods=['GET', 'POST'])
@login_required
def cadastrar_autorizado():
    if current_user.nivel_acesso != 'pais':
        flash('Acesso não autorizado.', 'danger')
        return redirect(url_for('login'))

    responsavel = Responsavel.query.filter_by(usuario_id=current_user.id).first()

    if request.method == 'POST':
        nome = request.form.get('nome')
        grau_parentesco = request.form.get('grau_parentesco')
        # Se você estiver salvando foto ou texto, pode capturar aqui também

        novo_autorizado = Autorizado(
            responsavel_id=responsavel.id,
            nome=nome,
            grau_parentesco=grau_parentesco
        )

        db.session.add(novo_autorizado)
        db.session.commit()

        flash('Autorizado cadastrado com sucesso!', 'success')
        return redirect(url_for('pais'))

    return render_template('autorizado_cadastro.html')

@app.route('/pais/autorizado/remover/<int:id>', methods=['POST'])
@login_required
def remover_autorizado(id):
    if current_user.nivel_acesso != 'pais':
        flash('Acesso não autorizado.', 'danger')
        return redirect(url_for('login'))

    responsavel = Responsavel.query.filter_by(usuario_id=current_user.id).first()

    autorizado = Autorizado.query.filter_by(id=id, responsavel_id=responsavel.id).first_or_404()

    db.session.delete(autorizado)
    db.session.commit()

    flash('Autorizado removido com sucesso!', 'success')
    return redirect(url_for('pais'))

@app.route('/secretaria')
@login_required
def secretaria():
    if current_user.nivel_acesso not in ['secretaria', 'diretoria']:
        flash('Acesso não autorizado.', 'danger')
        return redirect(url_for('login'))

    termo_busca = request.args.get('busca', '')

    if termo_busca:
        alunos = Aluno.query.filter(Aluno.nome.ilike(f'%{termo_busca}%')).all()
    else:
        alunos = Aluno.query.all()

    return render_template('secretaria.html', alunos=alunos, termo_busca=termo_busca)

@app.route('/secretaria/cadastrar-responsavel')
@login_required
def tela_cadastro_responsavel():
    if current_user.nivel_acesso not in ['diretoria', 'secretaria']:
        flash('Acesso não autorizado.', 'danger')
        return redirect(url_for('login'))

    return render_template('pais_cadastro.html')

@app.route('/secretaria/cadastrar-responsavel', methods=['POST'])
@login_required
def cadastrar_responsavel():
    if current_user.nivel_acesso not in ['diretoria', 'secretaria']:
        flash('Acesso não autorizado.', 'danger')
        return redirect(url_for('login'))

    nome = request.form.get('nome')
    email = request.form.get('email')
    senha = request.form.get('senha')

    if Usuario.query.filter_by(email=email).first():
        flash('Erro: Este e-mail já está cadastrado no sistema!', 'warning')
        return redirect(url_for('tela_cadastro_responsavel'))

    try:
        novo_usuario = Usuario(
            nome=nome,
            email=email,
            nivel_acesso='pais'
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

        registrar_log(
            usuario_id=current_user.id,
            acao='CADASTRO_RESPONSAVEL',
            detalhes=f"Cadastrou o responsável '{nome}'"
        )

        db.session.commit()

        flash(f'Responsável {nome} cadastrado com sucesso!', 'success')
        return redirect(url_for('secretaria'))

    except Exception as e:
        db.session.rollback()
        flash('Erro ao realizar o cadastro. Tente novamente.', 'danger')
        return redirect(url_for('tela_cadastro_responsavel'))

@app.route('/aluno/cadastrar', methods=['GET', 'POST'])
@login_required
def cadastrar_aluno():
    if current_user.nivel_acesso not in ['secretaria', 'diretoria']:
        flash('Acesso não autorizado.', 'danger')
        return redirect(url_for('login'))

    if request.method == 'POST':
        nome = request.form.get('nome')
        turma = request.form.get('turma')
        numero_matricula = request.form.get('numero_matricula')
        responsavel_id = request.form.get('responsavel_id')

        novo_aluno = Aluno(
            nome=nome,
            turma=turma,
            numero_matricula=numero_matricula,
            responsavel_id=responsavel_id
        )

        db.session.add(novo_aluno)
        db.session.commit()

        flash(f'Aluno {nome} cadastrado com sucesso!', 'success')
        return redirect(url_for('secretaria'))

    responsaveis = Responsavel.query.all()
    return render_template('aluno_cadastro.html', responsaveis=responsaveis)

@app.route('/logout')
@login_required
def logout():
    registrar_log(
        usuario_id=current_user.id,
        acao='LOGOUT',
        detalhes=f"Usuário '{current_user.nome}' encerrou a sessão."
    )
    logout_user()
    flash('Sessão encerrada.', 'info')
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)