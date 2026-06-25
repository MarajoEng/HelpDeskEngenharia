# Portal de Chamados Engenharia

Base inicial do projeto organizada em `backend/` e `frontend/`, com fundacao web na FASE 1 e persistencia preparada na FASE 2.

## Escopo atual

- Backend com FastAPI, SQLAlchemy, Alembic e migration inicial.
- Frontend com React, TypeScript, Vite e layout base.
- Arquivos de configuracao local para ambiente e banco.

## Estrutura

- `backend/`: API, models SQLAlchemy, migrations e testes.
- `frontend/`: aplicacao React com Vite.
- `.env.example`: variaveis iniciais de ambiente, incluindo `DATABASE_URL`.

## Comandos principais

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
alembic upgrade head
pytest
```

```bash
cd frontend
npm install
npm run dev
```
