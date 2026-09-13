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

## Subindo o ambiente

1. Construa e suba os containers:

   ```bash
   docker compose up --build
   ```

2. Após a criação dos containers, aguarde o serviço do banco de dados estar disponível e importe o dump/script inicial:

   ```bash
   docker compose exec -T db psql -U admin -d sccp_db < bd.sql
   ```

3. Nas execuções seguintes, basta subir os containers normalmente:

   ```bash
   docker compose up
   ```

## Estrutura básica de uso

- `requirements.txt` — dependências Python do projeto.
- `bd.sql` — script de criação/carga inicial do banco de dados.
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

- O usuário do banco configurado é `admin` e o banco de dados é `sccp_db`.
- Certifique-se de que a porta configurada para o banco não esteja em uso por outro serviço local antes de subir os containers.
