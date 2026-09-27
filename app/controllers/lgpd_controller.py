from flask import Blueprint, render_template

lgpd_bp = Blueprint('lgpd', __name__)

VERSAO_TERMOS = '1.0'


@lgpd_bp.route('/termos-de-uso')
def termos_de_uso():
    return render_template('termos_de_uso.html', versao=VERSAO_TERMOS)


@lgpd_bp.route('/politica-de-privacidade')
def politica_privacidade():
    return render_template('politica_privacidade.html', versao=VERSAO_TERMOS)