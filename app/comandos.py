import click

from app.extensions import db
from app.models import Usuario


def registrar_comandos(app):

    @app.cli.command('criar-usuario')
    @click.argument('nome')
    @click.argument('email')
    @click.argument('nivel_acesso', type=click.Choice(['secretaria', 'diretoria']))
    @click.password_option(prompt='Senha')
    def criar_usuario(nome, email, nivel_acesso, password):
        """Cria um usuário da secretaria ou da diretoria (responsáveis são cadastrados pelo sistema)."""
        if Usuario.query.filter_by(email=email).first():
            click.echo('Já existe um usuário com esse e-mail.')
            return

        usuario = Usuario(nome=nome, email=email, nivel_acesso=nivel_acesso)
        usuario.set_senha(password)
        db.session.add(usuario)
        db.session.commit()

        click.echo(f"Usuário '{nome}' ({nivel_acesso}) criado com sucesso.")
