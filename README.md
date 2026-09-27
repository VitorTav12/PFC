## Baixar
- [Python 3.x](https://www.python.org/) e `pip`
- [Docker](https://www.docker.com/) e [Docker Compose](https://docs.docker.com/compose/)

## Instalação

1. Clone o repositório:

   ```bash
   git clone <url-do-repositorio>
   cd <nome-do-repositorio>
   ```

2. Instale as dependências Python:

   ```bash
   pip install -r requirements.txt
   ```

3. Crie o arquivo `.env` a partir do exemplo e preencha os valores (chave secreta e senha do banco):

   ```bash
   cp .env.example .env
   ```

   Para gerar a `SECRET_KEY`:

   ```bash
   python -c "import secrets; print(secrets.token_hex(32))"
   ```

## Subindo o ambiente

1. Construa e suba os containers:

   ```bash
   docker compose up --build
   ```

2. Após a criação dos containers, aguarde o serviço do banco de dados estar disponível e importe o dump/script inicial:

   ```bash
   docker compose exec -T db psql -U admin -d sccp_db < bd.sql
   ```

3. Se o banco já existia antes de uma atualização do projeto, aplique as migrações da pasta `migracoes/` (uma única vez, em ordem):

```bash
   docker compose exec -T db psql -U admin -d sccp_db < migracoes/001_primeiro_acesso.sql
   docker compose exec -T db psql -U admin -d sccp_db < migracoes/002_recuperacao_senha.sql
   docker compose exec -T db psql -U admin -d sccp_db < migracoes/003_email_minusculo.sql
```

4. Nas execuções seguintes, basta subir os containers normalmente:

## Estrutura do projeto (MVC)

- `run.py` — ponto de entrada da aplicação.
- `config.py` — configurações lidas do `.env`.
- `app/models/` — **Model**: classes do banco (SQLAlchemy) e regras de negócio.
- `app/controllers/` — **Controller**: rotas separadas por perfil (Blueprints `auth`, `responsavel` e `secretaria`).
- `app/templates/` — **View**: páginas HTML (Jinja2 + Bootstrap).
- `app/static/` — arquivos estáticos (CSS).
- `uploads/` — fotos dos autorizados (fora do GitHub e fora da pasta pública).
- `requirements.txt` — dependências Python do projeto.
- `bd.sql` — script de criação/carga inicial do banco de dados.
- `docs/` — documentação técnica (integração com a API externa de e-mail).
- `migracoes/` — alterações no banco para quem já tinha criado o banco com uma versão anterior do `bd.sql`.
- `docker-compose.yml` — definição dos serviços (aplicação, banco de dados, etc).

## Parar o ambiente

Para parar os containers:

```bash
docker compose down
```

Para parar e remover volumes (isso apaga os dados do banco):

```bash
docker compose down -v
```

## Observações

- Usuário, senha e nome do banco ficam no `.env` (padrão do exemplo: usuário `admin` e banco `sccp_db`).
- Certifique-se de que a porta configurada para o banco não esteja em uso por outro serviço local antes de subir os containers.
