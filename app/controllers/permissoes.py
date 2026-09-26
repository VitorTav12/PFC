from functools import wraps

from flask import flash, redirect, url_for
from flask_login import current_user


def perfil_requerido(*perfis):
    # Usar sempre abaixo do @login_required
    def decorador(view):
        @wraps(view)
        def wrapper(*args, **kwargs):
            if current_user.nivel_acesso not in perfis:
                flash('Acesso não autorizado.', 'danger')
                return redirect(url_for('auth.login'))
            return view(*args, **kwargs)
        return wrapper
    return decorador
