# Portal de Chamados Engenharia

Base do projeto organizada em `backend/` e `frontend/`, com fundacao web na FASE 1, persistencia nas FASES 2 e 2.1, autenticacao na FASE 3, cadastro administrativo na FASE 4, abertura de chamados na FASE 5, listagem/detalhe na FASE 6, triagem da engenharia na FASE 7 e aprovacao de orcamento por alcada configuravel na FASE 8.

## Escopo atual

- Backend com FastAPI, SQLAlchemy, Alembic, triagem tecnica auditavel e aprovacao de orcamento por alcadas configuradas em banco.
- Backend com login JWT, hash de senha, usuario autenticado, CRUD administrativo de unidades/usuarios, abertura de chamados, filtros de fila da engenharia e autorizacao por perfil.
- Frontend com React, TypeScript, Vite, login, listagens paginadas, fila da engenharia, gestao administrativa de alcadas e fluxo de aprovacao pelo detalhe do chamado.
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

## Permissoes desta fase

- `admin`: gerencia unidades, usuarios e alcadas de aprovacao.
- `engineering` e `director`: consultam unidades.
- `manager`: consulta apenas a propria unidade no detalhe.
- `admin`, `engineering` e `director`: abrem e consultam chamados.
- `admin` e `engineering`: executam triagem tecnica pela fila `Engenharia` ou pelo detalhe do chamado.
- `admin` e `engineering`: podem solicitar aprovacao em chamados `triage` com `requires_approval=true`.
- `director` e demais perfis presentes em `approval_levels.allowed_roles`: podem aprovar ou reprovar apenas dentro da alcada configurada para o valor solicitado.
- `manager`: abre e consulta chamados apenas da propria unidade.
- `supplier`: nao participa dos chamados nesta fase.

## Limitacoes preservadas

- sem execucao
- sem encerramento
- sem upload
- sem dashboard
- sem relatorios
- sem Celery
