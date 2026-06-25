# Frontend

React + TypeScript + Vite para o Portal de Chamados Engenharia com autenticacao (FASE 3), cadastros (FASE 4), abertura (FASE 5), listagem/detalhe avancado (FASE 6), triagem (FASE 7), aprovacao (FASE 8), execucao (FASE 9), encerramento com evidencia (FASE 10) e dashboard operacional (FASE 11).

## Estrutura

- `src/App.tsx`: roteamento com protecao inicial de sessao.
- `src/hooks/useAuth.tsx`: contexto de autenticacao, token e logout.
- `src/api/authApi.ts`: integracao com `/auth/login` e `/auth/me`.
- `src/api/unitApi.ts`: integracao com `/units`.
- `src/api/userApi.ts`: integracao com `/users`.
- `src/api/approvalLevelApi.ts`: integracao administrativa com `/approval-levels`.
- `src/api/ticketApi.ts`: integracao com `/tickets`.
- `src/api/attachmentApi.ts`: upload, listagem e download de evidencias.
- `src/api/dashboardApi.ts`: integracao com `/dashboard/overview`.
- `src/pages/LoginPage.tsx`: tela de login.
- `src/pages/CreateTicketPage.tsx`: abertura de chamado.
- `src/pages/EngineeringQueuePage.tsx`: fila da engenharia com filtros, cards de resumo e acao de triagem.
- `src/pages/DashboardPage.tsx`: dashboard executivo e operacional com filtros, cards, rankings e SLA.
- `src/pages/TicketsPage.tsx`: listagem paginada com filtros avancados (busca textual, only_late, bicos parados, custo min/max).
- `src/pages/TicketDetailPage.tsx`: detalhe completo com indicadores finais, evidencias, historico e acoes de encerramento.
- `src/pages/ApprovalLevelsPage.tsx`: configuracao paginada de alcadas para `admin`.
- `src/pages/UnitsPage.tsx`: listagem e modal de criacao/edicao de unidades.
- `src/pages/UsersPage.tsx`: listagem e modal de criacao/edicao de usuarios.
- `src/components/tickets/TriageTicketModal.tsx`: formulario/modal de triagem integrado ao backend real.
- `src/components/tickets/RequestApprovalModal.tsx`: solicitacao de aprovacao de orcamento no detalhe.
- `src/components/tickets/ApprovalDecisionModal.tsx`: decisao de aprovacao ou reprovacao conforme a alcada pendente.
- `src/components/tickets/EvidenceSection.tsx`: secao de evidencias com upload/download.
- `src/components/tickets/ResolveTicketModal.tsx`: resolucao tecnica com custo final.
- `src/components/tickets/CloseTicketModal.tsx`: fechamento final auditavel.
- `src/components/layout/AppLayout.tsx`: shell com sidebar e topbar para usuario logado.
- `src/pages/HomePage.tsx`: area inicial autenticada.
- `src/styles/global.css`: identidade visual e estados base.

## Variaveis

Use `VITE_API_BASE_URL` para apontar o frontend para a API.

Exemplo:

```env
VITE_API_BASE_URL=http://127.0.0.1:8000
```

## Executar

```bash
cd frontend
npm install
npm run dev
```

## Build

```bash
cd frontend
npm run build
```

## Testar login

1. Rode o backend com as variaveis de ambiente configuradas.
2. Crie o admin dev com `python scripts/create_admin.py` dentro de `backend/`.
3. Abra o frontend e entre com `admin@local.test` / `admin123`.

## Testar cadastros e chamados

1. Entre com um usuario `admin`.
2. Use a sidebar para acessar `Unidades` e `Usuarios`.
3. Valide filtros, paginacao e os modais de criacao/edicao consumindo a API real.
4. Acesse `Chamados` para testar filtros avancados e paginacao.
5. Acesse `Abrir chamado` para criar um ticket real via `POST /tickets`.
6. Acesse `Engenharia` para validar a fila `queue=engineering`, filtros e cards de resumo.
7. Clique em `Fazer triagem` na fila ou no detalhe para atualizar responsavel, prioridade, severidade, SLA e comentario tecnico.
8. Em um ticket com `requires_approval=true`, solicite aprovacao pelo detalhe informando valor e justificativa.
9. Entre com um perfil permitido pela alcada para aprovar ou reprovar e valide o refresh do detalhe.
10. Inicie execucao e registre progresso quando o ticket estiver apto.
11. Envie evidencias na secao `Evidencias`, usando `closing_evidence` antes de resolver.
12. Resolva o chamado com descricao da solucao e custo final.
13. Feche o chamado com comentario final.
14. Acesse `Alcadas` como `admin` para criar, editar, filtrar e inativar niveis de aprovacao.

## Filtros de chamados disponiveis (FASE 6)

- Busca textual: numero, titulo, descricao, tipo do problema e nome/codigo da unidade
- Unidade, status, categoria, prioridade, severidade
- Custo minimo e maximo estimado
- Somente atrasados (SLA vencido)
- Com bicos parados

## Detalhe do chamado (FASE 6)

- Indicadores calculados: `elapsed_hours`, `is_late`, `sla_status`, `estimated_loss_total`
- Historico em timeline com usuario, transicao de status e comentario
- Dados completos da unidade (cidade, estado)
- Solicitante e responsavel

## Triagem da engenharia (FASE 7)

- Sidebar com entrada `Engenharia` apenas para `admin` e `engineering`
- Fila da engenharia consumindo `GET /tickets?queue=engineering`
- Modal simples de triagem com:
  - responsavel tecnico
  - prioridade
  - severidade
  - SLA previsto
  - exige aprovacao
  - comentario tecnico obrigatorio
- Carregamento dos responsaveis tecnicos via `GET /tickets/triage-assignees`
- Atualizacao imediata da listagem e do detalhe apos `PATCH /tickets/{ticket_id}/triage`
- Tratamento visual para erros de permissao e transicao invalida

## Aprovacao por alcada (FASE 8)

- Sidebar com entrada `Alcadas` apenas para `admin`
- Tela administrativa com tabela paginada, busca, filtro por ativo e modal de criar/editar
- Campos de alcada:
  - nome
  - valor minimo
  - valor maximo opcional
  - roles permitidas
  - status ativo
- Detalhe do chamado com secao de aprovacoes exibindo:
  - valor solicitado
  - valor aprovado
  - alcada aplicada
  - roles permitidas
  - solicitante e aprovador
  - justificativa e datas
- `admin` e `engineering` podem solicitar aprovacao apenas quando o ticket estiver em `triage` e com `requires_approval=true`
- A decisao de aprovar ou reprovar so aparece para usuarios cujo perfil esteja dentro da alcada pendente
- Quando o perfil logado nao tem alcada para o valor, a interface mostra a mensagem `Seu perfil nao possui alcada para aprovar este valor.`

## Permissoes

- `admin`, `engineering` e `director`: abrem e consultam todos os chamados.
- `admin` e `engineering`: acessam a fila `Engenharia` e executam triagem.
- `admin`: acessa `Alcadas` para configurar niveis de aprovacao.
- `admin` e `engineering`: podem solicitar aprovacao.
- `admin` e `engineering`: podem resolver e fechar chamados.
- `admin`, `engineering` e `manager` da propria unidade: podem enviar evidencias.
- `director`: pode visualizar evidencias, mas nao envia e nao encerra.
- `director` e demais roles configuradas em alcada ativa: podem decidir aprovacoes compativeis.
- `manager`: restritos a chamados da propria unidade.
- `supplier`: sem acesso a chamados nesta fase.

## Encerramento com evidencia (FASE 10)

- Secao `Evidencias` no detalhe com upload de imagens/PDF e download autenticado
- Botao `Resolver chamado` apenas para `admin` e `engineering` em `in_progress`
- Aviso visual quando falta `closing_evidence`
- Botao `Fechar chamado` apenas para `admin` e `engineering` em `resolved`
- Listagem principal com `resolved_at`, `closed_at`, `final_cost` e indicador de evidencia final

## Dashboard operacional (FASE 11)

- Rota principal autenticada em `/dashboard`
- Consumo real de `GET /dashboard/overview`
- Filtros de periodo, unidade, regiao, status e categoria
- Cards executivos com volume, SLA, custos e bicos parados
- Distribuicoes por status, categoria, prioridade e severidade
- Rankings de unidades por volume, custo e impacto operacional
- Preview de chamados atrasados com link para detalhe
- `manager` opera sempre no escopo da propria unidade

## Limitacoes desta fase

- sem relatorios
- sem Celery
- sem notificacoes
- sem IA
- sem storage externo
