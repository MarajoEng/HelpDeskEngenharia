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
- triagem, aprovacao, anexos, comentarios e mudanca manual de status ficam fora desta fase.

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
