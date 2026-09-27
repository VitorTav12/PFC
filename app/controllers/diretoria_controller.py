from datetime import datetime, timedelta

from flask import Blueprint, render_template
from flask_login import login_required

from app.models import Aluno, Responsavel, Autorizado, Movimentacao, Usuario, AuditoriaLog
from app.controllers.permissoes import perfil_requerido

diretoria_bp = Blueprint('diretoria', __name__, url_prefix='/diretoria')


@diretoria_bp.route('/')
@login_required
@perfil_requerido('diretoria')
def painel():
    agora = datetime.now()
    inicio_do_dia = agora.replace(hour=0, minute=0, second=0, microsecond=0)
    ultimos_7_dias = inicio_do_dia - timedelta(days=6)

    indicadores = {
        'alunos': Aluno.query.count(),
        'responsaveis': Responsavel.query.count(),
        'autorizados': Autorizado.query.count(),
        'retiradas_hoje': Movimentacao.query.filter(Movimentacao.data == agora.date()).count(),
        'acessos_hoje': AuditoriaLog.contar('LOGIN_SUCESSO', inicio_do_dia),
        'falhas_7_dias': AuditoriaLog.contar('LOGIN_FALHA', ultimos_7_dias),
        'pendentes': Usuario.query.filter_by(nivel_acesso='pais', precisa_trocar_senha=True).count(),
    }

    dias = [(ultimos_7_dias + timedelta(days=i)).strftime('%d/%m') for i in range(7)]
    grafico = {
        'dias': dias,
        'sucessos': AuditoriaLog.contagem_diaria('LOGIN_SUCESSO'),
        'falhas': AuditoriaLog.contagem_diaria('LOGIN_FALHA'),
    }

    return render_template(
        'diretoria.html',
        indicadores=indicadores,
        grafico=grafico,
        eventos=AuditoriaLog.recentes(30)
    )