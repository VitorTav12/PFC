# Integração com API externa: envio de e-mail (Brevo)

## 1. Objetivo

O Portal de Controle de Saída consome a API de e-mails transacionais do **Brevo** para enviar o link de
**recuperação de senha** ao usuário que esqueceu a senha. O e-mail é o canal que comprova que a pessoa que
pede a nova senha é a dona da conta, sem que a escola precise conhecer ou redefinir a senha manualmente.

## 2. Dados da API

| Item | Valor |
|---|---|
| Fornecedor | Brevo |
| Endpoint | `POST https://api.brevo.com/v3/smtp/email` |
| Formato | JSON (`content-type: application/json`) |
| Autenticação | Chave de API enviada no cabeçalho `api-key` |
| Resposta de sucesso | `201 Created`, com o identificador da mensagem (`messageId`) |
| Tempo máximo de espera | 10 segundos |

## 3. Onde a integração está no código (MVC)

| Camada | Arquivo | Papel |
|---|---|---|
| Model | `app/models/email_brevo.py` | Monta a requisição, chama a API e trata as respostas e falhas |
| Model | `app/models/token_recuperacao.py` | Gera o token, guarda só o hash, controla validade e uso único |
| Controller | `app/controllers/auth_controller.py` | Rotas `/esqueci-senha` e `/redefinir-senha/<token>` |
| View | `app/templates/emails/recuperacao_senha.html` | Corpo do e-mail enviado |
| View | `app/templates/esqueci_senha.html` e `redefinir_senha.html` | Telas do fluxo |

O acesso à API externa fica na camada Model pelo mesmo motivo que o acesso ao banco de dados: o Model é
responsável pelas fontes de dados e serviços que o sistema usa. O Controller apenas chama o método `enviar`
e decide o que mostrar ao usuário.

## 4. Fluxo

1. O usuário clica em **Esqueci minha senha** e informa o e-mail.
2. Se o e-mail existir, o sistema:
   - invalida links anteriores ainda não usados;
   - gera um token aleatório de 256 bits (`secrets.token_urlsafe(32)`);
   - guarda no banco **apenas o hash SHA-256** do token, com validade de 30 minutos;
   - registra `RECUPERACAO_SOLICITADA` na auditoria;
   - chama a API do Brevo com o link contendo o token.
3. A tela mostra sempre a mesma mensagem, exista o e-mail ou não. Isso impede que alguém descubra quais
   e-mails estão cadastrados.
4. Ao abrir o link, o sistema calcula o hash do token recebido e procura no banco. Se não existir, estiver
   expirado ou já tiver sido usado, o link é recusado e a tentativa é registrada.
5. Com o link válido, o usuário cria a nova senha, o token é marcado como usado e a ação
   `RECUPERACAO_CONCLUIDA` é registrada.

## 5. Exemplo de requisição

```http
POST /v3/smtp/email HTTP/1.1
Host: api.brevo.com
api-key: <BREVO_API_KEY>
accept: application/json
content-type: application/json

{
  "sender": { "name": "Portal de Controle de Saída", "email": "<EMAIL_REMETENTE>" },
  "to": [{ "email": "responsavel@exemplo.com", "name": "Nome do responsável" }],
  "subject": "Recuperação de senha",
  "htmlContent": "<html>... link de recuperação ...</html>",
  "textContent": "Olá ... link de recuperação ..."
}
```

## 6. Tratamento de respostas e falhas

| Situação | Comportamento do sistema |
|---|---|
| `201` / `200` / `202` | E-mail aceito pelo Brevo |
| Erro HTTP (`400`, `401` etc.) | Registra o código no log da aplicação e `RECUPERACAO_EMAIL_FALHOU` na auditoria |
| Sem conexão ou tempo esgotado | Mesmo tratamento acima; o sistema continua funcionando |
| Chave não configurada | Modo desenvolvimento: o e-mail não é enviado e o conteúdo, com o link, aparece no log do container |

Em nenhum caso a falha da API derruba a aplicação ou revela ao usuário se o e-mail existe.

## 7. Configuração

No arquivo `.env` (nunca versionado):

```
BREVO_API_KEY=chave gerada no painel do Brevo
EMAIL_REMETENTE=e-mail cadastrado e verificado como remetente no Brevo
EMAIL_REMETENTE_NOME=Portal de Controle de Saída
```

Depois de alterar o `.env`, é preciso recriar o container: `docker compose up -d --force-recreate web`.

## 8. Segurança

- A chave da API fica apenas no `.env` e não aparece em logs.
- O token de recuperação nunca é guardado em texto: um vazamento do banco não permite usar os links.
- Validade curta (30 minutos), uso único e invalidação dos links anteriores a cada novo pedido.
- Resposta idêntica para e-mails cadastrados e não cadastrados.
- Todas as etapas ficam registradas na auditoria: `RECUPERACAO_SOLICITADA`, `RECUPERACAO_EMAIL_DESCONHECIDO`,
  `RECUPERACAO_EMAIL_FALHOU`, `RECUPERACAO_LINK_INVALIDO` e `RECUPERACAO_CONCLUIDA`.

## 9. LGPD

Somente nome, e-mail e o link temporário são enviados ao Brevo. Nenhum dado de crianças, autorizados, fotos
ou registros de retirada sai do sistema. O compartilhamento está descrito no item 6 da Política de
Privacidade, disponível no próprio sistema.

## 10. Como testar

1. Na tela de login, clicar em **Esqueci minha senha** e informar o e-mail de um usuário existente.
2. Com a chave configurada: abrir o e-mail recebido. Sem a chave: ver o link com `docker compose logs web`.
3. Abrir o link e criar uma nova senha; entrar com ela.
4. Abrir o mesmo link de novo: deve ser recusado (uso único).
5. Conferir a auditoria:

```sql
SELECT acao, detalhes, data_horario FROM auditoria_log
WHERE acao LIKE 'RECUPERACAO%' ORDER BY id DESC;
```