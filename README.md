# Portal de Chamados Engenharia

Base do projeto organizada em `backend/` e `frontend/`, com fundacao web na FASE 1, persistencia nas FASES 2 e 2.1, autenticacao na FASE 3, cadastro administrativo na FASE 4, abertura de chamados na FASE 5, listagem/detalhe na FASE 6, triagem na FASE 7, aprovacao na FASE 8, execucao na FASE 9, encerramento auditavel na FASE 10, dashboard operacional na FASE 11, alertas/auditoria nas FASES 12 e 13, padrao visual profissional na FASE 14 e relatorios com exportacao CSV na FASE 15.

## Escopo atual

- Backend com FastAPI, SQLAlchemy, Alembic, login JWT, CRUD administrativo, fluxo de abertura, triagem, aprovacao, execucao, anexos locais, encerramento e dashboard com agregacoes reais do banco.
- Backend com FastAPI, SQLAlchemy, Alembic, login JWT, CRUD administrativo, fluxo de abertura, triagem, aprovacao, execucao, anexos locais, encerramento, dashboard e relatorios paginados/exportaveis com filtros aplicados no banco.
- Frontend com React, TypeScript e Vite, com listagens paginadas, fila da engenharia, detalhe completo, evidencias, resolucao, fechamento final, dashboard executivo/operacional e tela de relatorios com exportacao CSV.
- Frontend com camada `src/components/ui/` para layout, estados, tabelas, badges, modais e formularios padronizados sem dependencia de framework pesado de UI.
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

## Login local ponta a ponta

```bash
cd backend
source .venv/bin/activate
alembic upgrade head
python scripts/seed_demo.py
uvicorn app.main:app --reload
```

```bash
cd frontend
npm install
npm run dev
```

- Frontend local: `http://127.0.0.1:5173/login`
- Backend local: `http://127.0.0.1:8000`
- Credencial demo: `admin@local.test` / `admin123`

Troubleshooting de CORS:

- `CORS_ORIGINS` aceita lista separada por virgula ou JSON array.
- Em desenvolvimento, mantenha `http://localhost:5173` e `http://127.0.0.1:5173`.
- Em production, nao use `*`.
- Se `POST /auth/login` responder `500`, valide primeiro se o backend consegue ler enums do PostgreSQL e se o seed demo foi aplicado.

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

## FASE 14 — UX profissional do frontend

- Sidebar agrupada por area com topbar de sessao, logout claro e responsividade basica.
- Componentes reutilizaveis em `frontend/src/components/ui/`.
- Badges padronizados para status, prioridade, severidade e estados operacionais.
- Tabelas com loading, vazio, erro, acao e paginacao consistente nas telas principais.
- Formularios e modais administrativos/operacionais com labels visiveis e mensagens amigaveis.

## FASE 15 — Relatorios e exportacao CSV

- Endpoints protegidos em `GET /reports/tickets`, `/reports/costs`, `/reports/sla`, `/reports/units` e `/reports/suppliers`.
- Exportacao CSV correspondente em `/reports/*/export.csv`, sempre com UTF-8, cabecalho e respeito ao mesmo escopo/permissao da consulta.
- Perfis com acesso: `admin`, `director`, `engineering` e `manager`.
- `manager` opera sempre no escopo da propria unidade, inclusive na exportacao.
- `supplier` nao acessa relatarios nem exportacoes nesta fase.
- Filtros principais: periodo, unidade, regiao, status, categoria, prioridade, severidade, fornecedor, atraso, aprovacao e faixa de custo estimado.
- Limite de exportacao controlado por `REPORT_EXPORT_MAX_ROWS=5000`; se excedido, a API bloqueia a exportacao e orienta refinar os filtros.
- Auditoria registra `report_viewed` e `report_exported` com metadados seguros sobre tipo de relatorio, filtros e volume retornado/exportado.

## Limitacoes preservadas

- sem Celery
- sem notificacoes
- sem IA
- sem storage externo
