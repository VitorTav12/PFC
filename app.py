import os
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
login_manager.login_message = "Por favor, faça login para acessar esta página."
login_manager.login_message_category = "warning"

class Usuario(UserMixin, db.Model):
    __tablename__ = 'Usuarios'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String, nullable=False, unique=True)
    senha = db.Column(db.String(255), nullable=False)
    Nivel_de_acesso = db.Column(db.String(20), nullable=False)

    def set_senha(self, senha_texto_puro):
        self.senha = generate_password_hash(senha_texto_puro)

    def checar_senha(self, senha_digitada):
        if not self.senha:
            return False
        try:
            return check_password_hash(self.senha, senha_digitada)
        except Exception:
            return False

@login_manager.user_loader
def load_user(user_id):
    return Usuario.query.get(int(user_id))

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
        if current_user.Nivel_de_acesso == 'diretor':
            return redirect(url_for('secretaria'))

    if request.method == 'POST':
        email_input = request.form.get('email')
        senha_input = request.form.get('senha')

        usuario = Usuario.query.filter_by(email=email_input).first()

        if not usuario:
            flash('E-mail ou senha inválidos!', 'danger')
            return render_template('login.html')

        if usuario.checar_senha(senha_input):
            if usuario.Nivel_de_acesso == 'diretor':
                login_user(usuario)
                flash('Login de Direção efetuado!', 'success')
                return redirect(url_for('secretaria'))
            else:
                flash('Nesta fase, apenas a Direção tem acesso.', 'warning')
                return redirect(url_for('login'))
        else:
            flash('E-mail ou senha inválidos!', 'danger')

    return render_template('login.html')

@app.route('/pais')
def pais():
    return render_template("pais.html")

@app.route('/secretaria')
@login_required
def secretaria():
    if current_user.Nivel_de_acesso != 'diretor':
        flash('Acesso não autorizado.', 'danger')
        return redirect(url_for('login'))

    return render_template("secretaria.html")

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Sessão encerrada.', 'info')
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)