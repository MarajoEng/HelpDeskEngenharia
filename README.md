# Portal de Chamados Engenharia

Fundacao tecnica inicial do projeto, organizada em `backend/` e `frontend/`.

## Escopo desta fase

- Backend com FastAPI, configuracao por ambiente e health check.
- Frontend com React, TypeScript, Vite e layout inicial.
- Arquivos de base na raiz para onboarding e configuracao local.

## Estrutura

- `backend/`: aplicacao FastAPI, testes e dependencias Python.
- `frontend/`: aplicacao React com Vite.
- `.env.example`: variaveis iniciais do ambiente.

## Comandos principais

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
pytest
```

```bash
cd frontend
npm install
npm run dev
```
