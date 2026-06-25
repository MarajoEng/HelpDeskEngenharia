# Backend

Base do backend em FastAPI com SQLAlchemy e Alembic para o Portal de Chamados Engenharia, incluindo triagem tecnica da FASE 7, aprovacao da FASE 8, execucao da FASE 9, encerramento auditavel da FASE 10 e dashboard operacional da FASE 11.

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
MAX_UPLOAD_SIZE_MB=10
UPLOAD_DIR=uploads
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

Nao ha migration nova na FASE 10: `ticket_attachments` ja atende o contrato de evidencia e o Alembic continua em `head`.

## Contratos da FASE 2.1

- `tickets.severity`: enum controlado com `low`, `medium`, `high` e `critical`.
- `approvals.status`: enum controlado com `pending`, `approved`, `rejected` e `canceled`.
- `approval_levels`: tabela de alcadas por faixa de valor com roles autorizadas por nivel.
- A revision atual do Alembic passa a ser `0003`.

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

## Abertura de chamados da FASE 5

Endpoints de chamados:

- `POST /tickets`: cria chamado com `ticket_number` unico, `opened_at` automatico e historico inicial. Permitido para `admin`, `manager`, `engineering` e `director`.
- `GET /tickets`: lista paginada com filtros `unit_id`, `status`, `category`, `priority`, `severity`, `requires_approval`, `opened_from`, `opened_to`, `search`, `page` e `page_size`.
- `GET /tickets/{ticket_id}`: detalhe do chamado respeitando escopo por perfil.

Permissoes principais:

- `admin`, `engineering` e `director`: criam e consultam chamados de qualquer unidade ativa.
- `manager`: cria e consulta apenas chamados da propria unidade.
- `supplier`: bloqueado nesta fase.

Regras principais:

- todo chamado nasce com status `open`;
- `ticket_number` segue o formato `ENG-YYYYMMDD-000001`;
- `opened_by_user_id` vem do token autenticado;
- `assigned_to_user_id` inicia nulo;
- unidade precisa existir e estar ativa;
- valores numericos negativos sao rejeitados;
- se houver `fuel_nozzles_stopped` e `estimated_daily_loss`, a API retorna `estimated_loss_total`;
- triagem avancada, anexos, comentarios fora do fluxo oficial e mudanca manual de status continuam fora desta fase inicial de abertura.

Exemplo de criacao:

```json
{
  "unit_id": 1,
  "category": "fuel_pump",
  "problem_type": "Falha de pressao",
  "title": "Bomba principal sem operacao",
  "description": "A bomba principal da pista 2 parou de funcionar.",
  "priority": "high",
  "severity": "critical",
  "operational_impact": "Pista operando parcialmente.",
  "fuel_nozzles_stopped": 2,
  "estimated_daily_loss": "1500.00",
  "estimated_cost": "8000.00",
  "requires_approval": true
}
```

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

## Encerramento com evidencia da FASE 10

Endpoints:

- `POST /tickets/{ticket_id}/attachments`
- `GET /tickets/{ticket_id}/attachments`
- `GET /attachments/{attachment_id}/download`
- `PATCH /tickets/{ticket_id}/resolve`
- `PATCH /tickets/{ticket_id}/close`

Permissoes:

- Upload: `admin`, `engineering` e `manager` da propria unidade
- Listagem/download: `admin`, `engineering`, `director` e `manager` da propria unidade
- Resolucao/fechamento: `admin` e `engineering`
- `supplier`: bloqueado em anexos, resolucao e fechamento

Tipos de anexo:

- `opening_evidence`
- `progress_evidence`
- `closing_evidence`

Upload local:

- tipos permitidos: `image/jpeg`, `image/png`, `image/webp`, `application/pdf`
- limite padrao: `MAX_UPLOAD_SIZE_MB=10`
- diretorio local: `UPLOAD_DIR=uploads`
- `file_url` exposto ao cliente sempre aponta para `/attachments/{attachment_id}/download`

Payload de resolucao:

```json
{
  "solution_description": "Troca da conexao principal, teste hidraulico e liberacao operacional.",
  "final_cost": "489.90"
}
```

Payload de fechamento:

```json
{
  "close_comment": "Servico auditado e aceite final registrado pela engenharia."
}
```

Regras:

- resolver exige status `in_progress`, `solution_description`, `final_cost >= 0` e pelo menos uma `closing_evidence`
- fechar exige status `resolved` e `close_comment`
- toda transicao gera `TicketHistory`
- o detalhe do chamado retorna `attachments`, `total_hours`, `resolution_hours`, `closure_hours`, `final_cost` e `has_closing_evidence`

Limitacoes preservadas:

- sem storage externo
- sem relatorios
- sem Celery
- sem notificacoes

## Dashboard operacional da FASE 11

### GET /dashboard/overview

Permissoes:

- `admin`, `engineering` e `director`: acesso a toda a rede
- `manager`: acesso apenas a dados da propria unidade
- `supplier`: bloqueado

Filtros disponiveis:

- `date_from`
- `date_to`
- `unit_id`
- `region`
- `status`
- `category`

Indicadores principais:

- contagem total e por status
- `late_tickets`
- `critical_tickets`
- `tickets_with_fuel_nozzles_stopped`
- `total_fuel_nozzles_stopped`
- `estimated_daily_loss_total`
- `estimated_cost_total`
- `approved_cost_total`
- `final_cost_total`
- `average_resolution_hours`
- `average_closure_hours`
- `sla_compliance_rate`

Blocos adicionais:

- `executive_cards`
- `ranking_units_by_tickets`
- `ranking_units_by_cost`
- `ranking_units_by_fuel_nozzles`
- `tickets_by_status`
- `tickets_by_category`
- `tickets_by_priority`
- `tickets_by_severity`
- `sla_summary`
- `late_tickets_preview`

Regras:

- agregacoes feitas no banco com SQLAlchemy
- previews e rankings limitados a 10
- sem `SELECT *`
- `manager` nao pode consultar `unit_id` diferente da propria unidade
- se nao houver dados, o endpoint retorna zeros e listas vazias

## Listagem e detalhe da FASE 6

Melhorias aplicadas nos endpoints de chamados:

### GET /tickets — filtros disponiveis

| Parametro | Tipo | Descricao |
|---|---|---|
| `unit_id` | int | Filtrar por unidade |
| `status` | enum | Status do chamado |
| `category` | enum | Categoria |
| `priority` | enum | Prioridade |
| `severity` | enum | Severidade |
| `requires_approval` | bool | Exige aprovacao |
| `opened_from` | datetime | Abertos a partir de |
| `opened_to` | datetime | Abertos ate |
| `search` | string | Busca em numero, titulo, descricao, tipo do problema e nome/codigo da unidade |
| `only_late` | bool | Somente chamados com SLA vencido e status nao finalizado |
| `has_fuel_nozzles_stopped` | bool | Somente chamados com bicos parados > 0 |
| `min_estimated_cost` | decimal | Custo estimado minimo (nao negativo) |
| `max_estimated_cost` | decimal | Custo estimado maximo (nao negativo) |
| `page` | int | Pagina |
| `page_size` | int | Itens por pagina (max 100) |

### Retorno enriquecido da listagem

Cada item da listagem inclui agora:

- `unit_code`, `unit_name`: dados da unidade sem N+1
- `opened_by_user_name`: nome do solicitante
- `assigned_to_user_name`: nome do responsavel (quando atribuido)

### GET /tickets/{ticket_id} — detalhe completo

Retorna `TicketDetailResponse` com:

- Todos os campos do chamado
- `unit`: objeto `TicketUnitSummary` com id, code, name, city, state
- `opened_by`: objeto `TicketUserSummary` com id e name
- `assigned_to`: objeto `TicketUserSummary` ou null
- `history`: lista de `TicketHistoryResponse` ordenada por data
- `indicators`: objeto `TicketIndicators` com:
  - `estimated_loss_total`: perda total calculada
  - `elapsed_hours`: horas decorridas desde abertura
  - `is_late`: booleano se SLA vencido e nao encerrado
  - `sla_status`: `on_track`, `late`, `no_sla` ou `closed`

### Regras de permissao

- `admin`, `engineering`, `director`: acessam todos os chamados
- `manager`: restritos a chamados da propria unidade
- `supplier`: bloqueado em listagem e detalhe

## Observacao de teste

Os testes de metadata, autenticacao, CRUD administrativo e chamados usam SQLite em memoria para validar estrutura, login, token, autorizacao, paginacao, filtros e indicadores sem depender de um PostgreSQL real.

## Triagem da engenharia na FASE 7

### PATCH /tickets/{ticket_id}/triage

Permissoes:

- `admin` e `engineering`: podem executar triagem
- `director`: pode visualizar, mas nao pode triar
- `manager` e `supplier`: bloqueados

Payload:

```json
{
  "assigned_to_user_id": 7,
  "priority": "medium",
  "severity": "high",
  "requires_approval": false,
  "sla_due_at": "2026-06-25T18:00:00Z",
  "technical_comment": "Analise tecnica iniciada pela engenharia central."
}
```

Retorno:

- `TicketDetailResponse` completo e atualizado, com `history` e `indicators`

Validacoes principais:

- `technical_comment` obrigatorio e sem valor vazio
- `assigned_to_user_id`, quando informado, precisa existir, estar ativo e ter role `engineering` ou `admin`
- `sla_due_at`, quando informado, nao pode estar no passado
- `priority` e `severity` seguem os enums existentes

Transicoes permitidas nesta fase:

- `open` -> `triage`
- `waiting_unit` -> `triage`
- `triage` -> `triage` para atualizacao tecnica adicional

Bloqueios desta fase:

- triagem nao pode partir de `closed`, `canceled`, `resolved`, `waiting_approval`, `approved`, `rejected`, `in_progress` e demais status fora do fluxo permitido
- toda tentativa invalida retorna `409`

Auditoria:

- toda triagem gera `TicketHistory`

## Aprovacao de orcamento na FASE 8

### ApprovalLevel

Tabela administrativa para definir a alcada de aprovacao por faixa de valor:

- `name`: nome operacional da alcada
- `min_amount`: valor minimo aceito
- `max_amount`: valor maximo ou `null` para topo aberto
- `allowed_roles`: lista JSON com os perfis autorizados a decidir
- `is_active`: inativacao logica

Regras:

- somente `admin` cria ou edita alcadas
- `admin`, `engineering` e `director` podem listar e visualizar alcadas
- faixas ativas nao podem se sobrepor
- valores negativos sao rejeitados

### Endpoints de alcada

- `GET /approval-levels`: lista paginada com `page`, `page_size`, `search` e `is_active`
- `POST /approval-levels`: cria alcada
- `GET /approval-levels/{approval_level_id}`: detalhe de uma alcada
- `PATCH /approval-levels/{approval_level_id}`: atualiza nome, faixa, roles permitidas e estado ativo

Payload de exemplo:

```json
{
  "name": "Diretoria ate 5000",
  "min_amount": "1000.01",
  "max_amount": "5000.00",
  "allowed_roles": ["director", "admin"],
  "is_active": true
}
```

### Seed dev/test

Script opcional e idempotente para ambientes locais:

```bash
cd backend
source .venv/bin/activate
python scripts/seed_approval_levels.py
```

O script nao executa em `production` e cria tres niveis padrao de alcada.

### Fluxo de aprovacao

#### POST /tickets/{ticket_id}/approval-request

Permissoes:

- `admin` e `engineering`

Regras:

- ticket precisa estar em `triage`
- `requires_approval` precisa ser `true`
- o valor solicitado precisa encontrar uma alcada ativa compativel
- nao pode existir `Approval` pendente para o ticket
- o ticket muda para `waiting_approval`
- `TicketHistory` e criado com a transicao

Payload:

```json
{
  "amount_requested": "3200.00",
  "justification": "Troca completa do conjunto hidraulico."
}
```

#### PATCH /tickets/{ticket_id}/approval-decision

Permissoes:

- qualquer usuario cujo `role` esteja dentro de `approval_levels.allowed_roles` da aprovacao pendente

Regras:

- ticket precisa estar em `waiting_approval`
- `manager` e `supplier` nao aprovam nesta fase
- `approved` atualiza `Approval`, `Ticket.approved_cost`, `Ticket.approved_at` e `Ticket.status=approved`
- `rejected` atualiza `Approval` e `Ticket.status=rejected`
- toda decisao gera `TicketHistory`

Payload:

```json
{
  "decision": "approved",
  "amount_approved": "3000.00",
  "justification": "Valor aprovado dentro da alcada da diretoria."
}
```

### GET /tickets/{ticket_id}

O detalhe do chamado passa a retornar `approvals` enriquecido com:

- dados do solicitante e aprovador
- alcada aplicada (`approval_level_id`, `approval_level_name`, `approval_allowed_roles`)
- valor solicitado, valor aprovado, status, justificativa e datas

## Limitacoes desta fase

- sem execucao do chamado
- sem encerramento
- sem upload
- sem dashboard
- sem relatorios
- sem Celery
- `old_status`, `new_status`, `user_id`, `comment` e `created_at` ficam registrados
- `triaged_at` e preenchido apenas na primeira entrada em `triage`

### GET /tickets?queue=engineering

Filtro adicional para a fila da engenharia usando a listagem existente:

- inclui apenas status `open`, `triage` e `waiting_unit`
- preserva paginacao, limite maximo e permissoes da listagem principal
- pode ser combinado com `unit_id`, `priority`, `severity`, `status`, `only_late` e demais filtros ja existentes

### GET /tickets/triage-assignees

Lista paginada de usuarios elegiveis para atribuicao tecnica:

- somente `admin` e `engineering`
- retorna apenas usuarios ativos com role `admin` ou `engineering`
- aceita `page`, `page_size` e `search`

### Limitacoes preservadas

- sem aprovacao de orcamento
- sem execucao
- sem encerramento
- sem upload
- sem dashboard
- sem relatorios
- sem Celery
