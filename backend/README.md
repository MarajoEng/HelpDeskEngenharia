# Backend

Base do backend em FastAPI com SQLAlchemy e Alembic para o Portal de Chamados Engenharia.

## Estrutura

- `app/main.py`: aplicacao FastAPI e rotas base.
- `app/core/config.py`: configuracao por variaveis de ambiente.
- `app/core/database.py`: engine e sessao SQLAlchemy.
- `app/models/`: models SQLAlchemy, enums e metadata compartilhada.
- `alembic/`: configuracao e revisions do banco.
- `tests/`: health check, metadata, enums e setup do Alembic.

## Configuracao

Defina `DATABASE_URL` em um arquivo `.env` dentro de `backend/` ou no ambiente.

Exemplo:

```env
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/helpdesk_engenharia
SECRET_KEY=change-me-in-dev
ACCESS_TOKEN_EXPIRE_MINUTES=60
ALGORITHM=HS256
```

## Instalar dependencias

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Executar API

```bash
cd backend
source .venv/bin/activate
uvicorn app.main:app --reload
```

## Rodar migrations

```bash
cd backend
source .venv/bin/activate
alembic upgrade head
```

## Contratos da FASE 2.1

- `tickets.severity`: enum controlado com `low`, `medium`, `high` e `critical`.
- `approvals.status`: enum controlado com `pending`, `approved`, `rejected` e `canceled`.
- A revision atual do Alembic passa a ser `0002`.

## Autenticacao da FASE 3

- `POST /auth/login`: recebe email e senha e retorna `access_token` JWT.
- `GET /auth/me`: exige bearer token valido e devolve o usuario autenticado.
- Usuario inativo nao consegue autenticar nem reutilizar token.
- Permissoes iniciais por perfil ficam centralizadas no backend via `require_roles`.

## Cadastro administrativo da FASE 4

Endpoints de unidades:

- `GET /units`: lista paginada com filtros `search`, `is_active`, `state`, `region`, `page`, `page_size` e `sort`.
- `POST /units`: cria unidade. Somente `admin`.
- `GET /units/{unit_id}`: detalhe. Permitido para `admin`, `engineering`, `director` e `manager` da propria unidade.
- `PATCH /units/{unit_id}`: atualiza unidade. Somente `admin`.

Endpoints de usuarios:

- `GET /users`: lista paginada com filtros `search`, `role`, `unit_id`, `is_active`, `page`, `page_size` e `sort`. Somente `admin`.
- `POST /users`: cria usuario com hash de senha. Somente `admin`.
- `GET /users/{user_id}`: detalhe. Permitido para `admin` ou o proprio usuario.
- `PATCH /users/{user_id}`: atualiza usuario. Somente `admin`.

Regras principais:

- nao existe exclusao fisica de unidade;
- `code` de unidade e `email` de usuario sao unicos;
- `manager` precisa de `unit_id`;
- `unit_id` informado precisa existir;
- toda listagem retorna `items`, `total`, `page`, `page_size` e `pages`.

## Criar admin de desenvolvimento

Uso apenas para ambiente local e testes.

```bash
cd backend
source .venv/bin/activate
python scripts/create_admin.py
```

Credenciais dev documentadas:

- email: `admin@local.test`
- password: `admin123`

## Rodar testes

```bash
cd backend
source .venv/bin/activate
pytest
```

## Observacao de teste

Os testes de metadata, autenticacao e CRUD administrativo usam SQLite em memoria para validar estrutura, login, token, autorizacao, paginacao e filtros sem depender de um PostgreSQL real.
