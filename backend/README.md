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

## Rodar testes

```bash
cd backend
source .venv/bin/activate
pytest
```

## Observacao de teste

Os testes de metadata usam SQLite apenas para validar a estrutura dos models sem depender de um PostgreSQL real.
