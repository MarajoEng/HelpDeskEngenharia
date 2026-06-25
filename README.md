# Portal de Chamados Engenharia

Base do projeto organizada em `backend/` e `frontend/`, com fundacao web na FASE 1, persistencia nas FASES 2 e 2.1, autenticacao na FASE 3, cadastro administrativo na FASE 4, abertura de chamados na FASE 5, listagem/detalhe na FASE 6, triagem na FASE 7, aprovacao na FASE 8, execucao na FASE 9, encerramento auditavel na FASE 10 e dashboard operacional na FASE 11.

## Escopo atual

- Backend com FastAPI, SQLAlchemy, Alembic, login JWT, CRUD administrativo, fluxo de abertura, triagem, aprovacao, execucao, anexos locais, encerramento e dashboard com agregacoes reais do banco.
- Frontend com React, TypeScript e Vite, com listagens paginadas, fila da engenharia, detalhe completo, evidencias, resolucao, fechamento final e dashboard executivo/operacional.
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
- `admin` e `engineering`: podem iniciar execucao, registrar progresso, resolver e fechar chamados.
- `admin`, `engineering` e `manager` da propria unidade: podem enviar evidencias.
- `admin`, `engineering` e `director`: acessam o dashboard de toda a rede.
- `manager`: acessa o dashboard apenas no escopo da propria unidade.
- `director`: visualiza evidencias, mas nao envia e nao encerra.
- `director` e demais perfis presentes em `approval_levels.allowed_roles`: podem aprovar ou reprovar apenas dentro da alcada configurada para o valor solicitado.
- `manager`: abre e consulta chamados apenas da propria unidade.
- `supplier`: nao participa dos chamados nesta fase.

## FASE 11 — Dashboard operacional

- Endpoint `GET /dashboard/overview` protegido por token
- Filtros: `date_from`, `date_to`, `unit_id`, `region`, `status`, `category`
- Indicadores reais de volume, SLA, custos, bicos parados, tickets criticos e atrasos
- Rankings limitados a top 10 por volume, custo e impacto operacional
- Preview limitada de chamados atrasados e distribuicoes por status/categoria/prioridade/severidade
- Home autenticada redireciona para `/dashboard`

## Limitacoes preservadas

- sem relatorios
- sem Celery
- sem notificacoes
- sem IA
- sem storage externo
