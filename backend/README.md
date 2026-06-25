# Backend

Base inicial em FastAPI para o Portal de Chamados Engenharia.

## Estrutura

- `app/main.py`: cria a aplicacao FastAPI.
- `app/core/config.py`: configuracao inicial por variaveis de ambiente.
- `app/api/routes/health_routes.py`: endpoint `GET /health/live`.
- `tests/test_health.py`: teste basico do health check.

## Executar

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## Testar

```bash
cd backend
pytest
```
