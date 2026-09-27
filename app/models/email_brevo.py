import json
import urllib.error
import urllib.request

from flask import current_app


class EmailBrevo:

    @staticmethod
    def enviar(destinatario_email, destinatario_nome, assunto, html, texto):
        chave = current_app.config.get('BREVO_API_KEY')

        if not chave:
            current_app.logger.warning(
                'BREVO_API_KEY não configurada: e-mail NÃO enviado (modo desenvolvimento).\n'
                'Para: %s\nAssunto: %s\n%s', destinatario_email, assunto, texto
            )
            return 'simulado'

        corpo = {
            'sender': {
                'name': current_app.config['EMAIL_REMETENTE_NOME'],
                'email': current_app.config['EMAIL_REMETENTE'],
            },
            'to': [{'email': destinatario_email, 'name': destinatario_nome}],
            'subject': assunto,
            'htmlContent': html,
            'textContent': texto,
        }

        requisicao = urllib.request.Request(
            current_app.config['BREVO_API_URL'],
            data=json.dumps(corpo).encode('utf-8'),
            method='POST',
            headers={
                'api-key': chave,
                'accept': 'application/json',
                'content-type': 'application/json',
            },
        )

        try:
            with urllib.request.urlopen(requisicao, timeout=10) as resposta:
                if resposta.status in (200, 201, 202):
                    return 'enviado'
                current_app.logger.error('Brevo respondeu com status inesperado: %s', resposta.status)
                return 'falhou'
        except urllib.error.HTTPError as erro:
            current_app.logger.error('Brevo recusou o envio (HTTP %s): %s', erro.code, erro.read()[:300])
            return 'falhou'
        except (urllib.error.URLError, TimeoutError) as erro:
            current_app.logger.error('Não foi possível conectar ao Brevo: %s', erro)
            return 'falhou'