from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def login():
    return render_template('login.html')

@app.route('/pais')
def pais():
    return render_template("pais.html")

@app.route('/secretaria')
def secretaria():
    return render_template("secretaria.html")

if __name__ == '__main__':
    app.run(debug=True)