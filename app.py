#Parte das importações das bibliotecas
import os 
from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text

#Parte das config
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = True

db = SQLAlchemy(app)

#Parte de Rotas
@app.route('/status')
def status_banco():
    try:
        db.session.execute(text('SELECT 1'))
        return {"status": "sucesso", "mensagem": "Conexão com PostgreSQL ativa e respondendo!"}, 200
    except Exception as e:
        return {"status": "erro", "mensagem": str(e)}, 500

@app.route('/')
def login():
    print("servidor iniciado")
    return render_template('login.html')

@app.route('/pais')
def pais():
    return render_template("pais.html")

@app.route('/secretaria')
def secretaria():
    return render_template("secretaria.html")

if __name__ == '__main__':
    app.run(debug=True)