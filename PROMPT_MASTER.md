# PROMPT_MASTER.md — Portal de Chamados Engenharia

Você é um desenvolvedor sênior full stack.

Atue com foco em arquitetura limpa, segurança, performance, rastreabilidade e manutenção futura.

## Projeto

Portal de Chamados de Engenharia e Manutenção Estrutural para rede de postos.

O sistema deve centralizar a abertura, triagem, aprovação, execução e encerramento de chamados críticos de engenharia e manutenção.

## Objetivo do sistema

Criar uma plataforma para controlar chamados relacionados a:

* bombas de combustível;
* bicos parados;
* vazamentos;
* canos estourados;
* falhas elétricas graves;
* infiltrações;
* avarias estruturais;
* cobertura danificada;
* pista interditada;
* risco ambiental;
* manutenções que ultrapassam orçamento local;
* demandas que exigem engenharia central.

## Stack obrigatória

Backend:

* Python
* FastAPI
* SQLAlchemy
* Alembic
* PostgreSQL
* Pydantic
* Pytest

Frontend:

* React
* TypeScript
* Vite
* React Router
* TanStack Query ou camada equivalente de hooks
* Componentes reutilizáveis

Infra:

* Redis
* Celery
* Worker
* Docker Compose para ambiente local

## Regras gerais obrigatórias

1. Trabalhe sempre por fase.
2. Não implemente fora do escopo da fase atual.
3. Antes de alterar código, leia a estrutura existente.
4. Não quebre telas, endpoints, migrations ou testes já existentes.
5. Não remova funcionalidades sem necessidade.
6. Não crie código duplicado quando já existir padrão no projeto.
7. Regra de negócio deve ficar no backend.
8. Frontend deve consumir API real, sem mock fixo em produção.
9. Não use SELECT *.
10. Toda listagem deve ter paginação.
11. Toda listagem deve ter limite máximo de registros.
12. Toda mudança de status deve gerar histórico.
13. Todo chamado deve registrar data/hora de abertura.
14. Todo encerramento deve exigir evidência.
15. Toda aprovação deve registrar usuário, data, valor e justificativa.
16. Toda ação crítica deve validar permissão no backend.
17. Não confiar apenas em bloqueio visual no frontend.
18. Criar testes para regras críticas.
19. Rodar validações possíveis antes de finalizar.
20. Ao final da fase, entregar relatório técnico.

## Padrão de qualidade

O código deve seguir:

* nomes claros;
* tipagem forte;
* funções pequenas;
* validações explícitas;
* tratamento de erro;
* migrations versionadas;
* queries performáticas;
* índices no banco;
* componentes reutilizáveis;
* layout profissional;
* logs úteis;
* sem gambiarra;
* sem regra crítica escondida no frontend;
* sem dashboard com número falso;
* sem endpoint sem validação.

## Estrutura esperada

Raiz do projeto:

* backend/
* frontend/
* docker-compose.yml
* .env.example
* README.md
* PROMPT_MASTER.md
* PHASES.md
* DESIGN.md

## Entidades principais

### User

Campos:

* id
* name
* email
* password_hash
* role
* unit_id
* is_active
* created_at
* updated_at

### Unit

Campos:

* id
* code
* name
* city
* state
* region
* is_active
* created_at
* updated_at

### Ticket

Campos:

* id
* ticket_number
* unit_id
* opened_by_user_id
* assigned_to_user_id
* category
* problem_type
* title
* description
* priority
* severity
* status
* operational_impact
* fuel_nozzles_stopped
* estimated_daily_loss
* estimated_cost
* approved_cost
* final_cost
* requires_approval
* opened_at
* triaged_at
* approved_at
* started_at
* resolved_at
* closed_at
* sla_due_at
* created_at
* updated_at

### TicketHistory

Campos:

* id
* ticket_id
* user_id
* old_status
* new_status
* comment
* created_at

### TicketAttachment

Campos:

* id
* ticket_id
* uploaded_by_user_id
* file_url
* file_type
* attachment_type
* created_at

### Approval

Campos:

* id
* ticket_id
* requested_by_user_id
* approved_by_user_id
* status
* amount_requested
* amount_approved
* justification
* approved_at
* created_at

### Supplier

Campos:

* id
* name
* document
* phone
* email
* specialty
* is_active
* created_at

## Perfis do sistema

Perfis obrigatórios:

* admin
* manager
* engineering
* director
* supplier

## Permissões gerais

### Admin

Pode:

* gerenciar usuários;
* gerenciar unidades;
* visualizar todos os chamados;
* configurar dados base;
* acessar auditoria.

### Manager

Pode:

* abrir chamados;
* anexar evidências;
* acompanhar chamados da própria unidade;
* responder solicitações;
* confirmar informações.

### Engineering

Pode:

* visualizar chamados da rede;
* fazer triagem;
* alterar prioridade;
* solicitar aprovação;
* atribuir responsável;
* acompanhar execução;
* encerrar chamados com evidência.

### Director

Pode:

* visualizar dashboard executivo;
* acompanhar custos;
* acompanhar SLA;
* aprovar quando necessário;
* consultar relatórios.

### Supplier

Pode futuramente:

* visualizar ordens vinculadas;
* atualizar andamento;
* anexar evidência de execução.

## Status dos chamados

Status obrigatórios:

* open
* triage
* waiting_approval
* approved
* rejected
* in_progress
* waiting_supplier
* waiting_unit
* resolved
* closed
* canceled

## Categorias iniciais

Categorias obrigatórias:

* fuel_pump
* fuel_nozzle
* electrical
* plumbing
* leak
* structure
* roof
* pavement
* environmental_risk
* other

## Prioridades

Prioridades obrigatórias:

* low
* medium
* high
* critical

## Regras de negócio obrigatórias

### Chamado

* Todo chamado nasce com status open.
* Todo chamado deve ter ticket_number único.
* Todo chamado deve registrar opened_at automaticamente.
* Todo chamado deve estar vinculado a uma unidade.
* Todo chamado deve estar vinculado ao usuário que abriu.
* Chamado crítico deve ser fácil de identificar.
* Chamado com bicos parados deve permitir informar quantidade.
* Chamado pode ter perda estimada por dia.
* Chamado pode exigir aprovação de orçamento.

### Histórico

* Toda alteração de status deve criar registro em TicketHistory.
* Histórico deve registrar usuário, data, status anterior, novo status e comentário.
* Não permitir alteração de status sem rastreabilidade.

### Aprovação

* Chamado que ultrapassa alçada da unidade deve ir para waiting_approval.
* Aprovação deve registrar valor solicitado.
* Aprovação deve registrar valor aprovado, quando houver.
* Aprovação deve registrar aprovador.
* Aprovação deve registrar data/hora.
* Reprovação deve exigir justificativa.

### Encerramento

* Chamado não pode ser encerrado sem descrição da solução.
* Chamado não pode ser encerrado sem evidência final.
* Encerramento deve registrar closed_at.
* Resolução deve registrar resolved_at.
* Sistema deve calcular tempo total do chamado.
* Sistema deve indicar se SLA foi cumprido ou estourado.

### Dashboard

* Dashboard deve usar dados reais do banco.
* Não criar números fixos no frontend.
* Indicadores devem vir da API.
* Queries agregadas devem ser performáticas.
* Listagens do dashboard devem ter limite.

## Performance

Regras obrigatórias:

* Não usar SELECT *.
* Usar paginação em todas as listagens.
* Usar filtros no banco, não em memória.
* Criar índices para campos de filtro.
* Evitar N+1 queries.
* Usar eager loading somente quando necessário.
* Consultar apenas campos necessários.
* Definir limite máximo de page_size.

Índices mínimos:

* users.email
* units.code
* tickets.unit_id
* tickets.status
* tickets.priority
* tickets.severity
* tickets.category
* tickets.opened_at
* tickets.closed_at
* tickets.sla_due_at
* tickets.requires_approval
* ticket_history.ticket_id
* approvals.ticket_id
* approvals.status

## Frontend

Regras obrigatórias:

* Usar React com TypeScript.
* Criar componentes reutilizáveis.
* Não duplicar layout.
* Não colocar regra crítica apenas no frontend.
* Usar camada de API organizada.
* Usar hooks para chamadas principais.
* Tratar loading, erro e empty state.
* Usar badges para status e prioridade.
* Usar confirmação em ações críticas.
* Não usar mock fixo em tela final.
* Seguir DESIGN.md.

Telas principais:

* Login
* Dashboard
* Chamados
* Abrir Chamado
* Detalhe do Chamado
* Fila da Engenharia
* Aprovações
* Unidades
* Usuários
* Relatórios

## Backend

Regras obrigatórias:

* Separar routes, schemas, models, services e repositories.
* Validar payloads com Pydantic.
* Tratar erros de forma padronizada.
* Proteger endpoints por autenticação.
* Proteger ações por permissão.
* Manter regra de negócio em services.
* Manter queries em repositories ou camada equivalente.
* Criar testes para services críticos.
* Usar migrations para mudanças no banco.

## Celery, Redis e Worker

Redis deve ser usado para:

* fila;
* cache quando necessário;
* suporte ao Celery.

Celery deve ser usado para:

* tarefas assíncronas;
* alertas de SLA;
* rotinas de verificação;
* relatórios demorados;
* processamento futuro de anexos;
* notificações futuras.

Não usar Celery para regra simples que pode ser resolvida diretamente na request.

## Segurança

Regras obrigatórias:

* Senha sempre com hash.
* Nunca salvar senha pura.
* JWT com expiração.
* Endpoints protegidos.
* Upload com validação de tipo e tamanho.
* Permissões validadas no backend.
* Erros não devem expor stack trace para usuário final.
* Dados sensíveis devem ser tratados com cuidado.
* Logs não devem vazar senha ou token.

## Testes

Criar testes para:

* autenticação;
* permissões;
* criação de chamado;
* alteração de status;
* histórico automático;
* aprovação;
* encerramento com evidência;
* filtros e paginação;
* dashboard;
* worker quando aplicável.

## Formato obrigatório de execução por fase

Ao receber uma fase:

1. Leia a estrutura atual do projeto.
2. Leia PROMPT_MASTER.md, PHASES.md e DESIGN.md se existirem.
3. Identifique arquivos relevantes.
4. Implemente somente o escopo da fase.
5. Crie ou ajuste testes.
6. Rode validações possíveis.
7. Corrija erros encontrados.
8. Entregue relatório final.

## Formato obrigatório do relatório final

Sempre finalizar com:

Status:
PASS, PASS_WITH_NOTES ou FAIL

Arquivos criados/alterados:

* ...

Resumo técnico:

* ...

Comandos executados:

* ...

Testes:

* ...

Observações:

* ...

Próxima fase sugerida:

* ...

## Restrições finais

Não avance para próxima fase sem solicitação.

Não misture fases.

Não implemente funcionalidades futuras antes da hora.

Não altere arquitetura sem justificar.

Não use soluções improvisadas quando houver alternativa limpa.

Não entregue apenas código sem explicar o que foi feito.

Não finalize sem relatório técnico.
