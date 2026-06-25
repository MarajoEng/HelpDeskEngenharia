# Portal de Chamados Engenharia

Base do projeto organizada em `backend/` e `frontend/`, com fundacao web na FASE 1, persistencia nas FASES 2 e 2.1 e autenticacao inicial na FASE 3.

## Escopo atual

- Backend com FastAPI, SQLAlchemy, Alembic e migration inicial.
- Backend com login JWT, hash de senha, usuario autenticado e autorizacao inicial por perfil.
- Frontend com React, TypeScript, Vite, tela de login e area autenticada base.
- Arquivos de configuracao local para ambiente e banco.

## Estrutura

- `backend/`: API, models SQLAlchemy, migrations e testes.
- `frontend/`: aplicacao React com Vite.
- `.env.example`: variaveis de backend e frontend, incluindo JWT e URL da API.

## Comandos principais

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
alembic upgrade head
pytest
python scripts/create_admin.py
```

```bash
cd frontend
npm install
npm run dev
npm run build
```

## Login local

- Crie o admin dev com `python scripts/create_admin.py` em `backend/`.
- Use `admin@local.test` e `admin123` apenas em desenvolvimento.
