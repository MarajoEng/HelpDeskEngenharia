# Frontend

React + TypeScript + Vite para o Portal de Chamados Engenharia com autenticacao (FASE 3), cadastros (FASE 4), abertura (FASE 5), listagem/detalhe avancado (FASE 6), triagem (FASE 7), aprovacao (FASE 8), execucao (FASE 9), encerramento com evidencia (FASE 10), dashboard operacional (FASE 11), alertas/auditoria (FASES 12 e 13), padrao visual profissional (FASE 14) e relatorios/exportacao CSV (FASE 15).

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
- `src/api/reportApi.ts`: integracao com `/reports` e exportacao CSV autenticada.
- `src/pages/LoginPage.tsx`: tela de login.
- `src/pages/CreateTicketPage.tsx`: abertura de chamado.
- `src/pages/EngineeringQueuePage.tsx`: fila da engenharia com filtros, cards de resumo e acao de triagem.
- `src/pages/DashboardPage.tsx`: dashboard executivo e operacional com filtros, cards, rankings e SLA.
- `src/pages/ReportsPage.tsx`: tela de relatorios com abas por tipo, filtros superiores, tabela paginada e exportacao CSV.
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
- `src/components/ui/`: biblioteca leve de componentes visuais reutilizaveis (`Button`, `Badge`, `Input`, `Select`, `Textarea`, `Modal`, `Table`, `Pagination`, `EmptyState`, `LoadingState`, `ErrorState`, `ConfirmDialog`, `PageHeader`, `FilterBar`, `StatCard`, `StatusBadge`, `PriorityBadge`, `SeverityBadge`).
- `src/utils/messages.ts`: normalizacao de mensagens operacionais e vazios padronizados.
- `src/utils/formatters.ts`: formatacao central de datas, moeda e campos `datetime-local`.
- `src/pages/HomePage.tsx`: area inicial autenticada.
- `src/styles/global.css`: identidade visual historica e classes legadas.
- `src/styles/ui.css`: consolidacao da FASE 14 para layout, formularios, tabelas, badges, modais e responsividade basica.

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

Fluxo local esperado:

- backend em `http://127.0.0.1:8000`
- frontend em `http://127.0.0.1:5173`
- login demo: `admin@local.test` / `admin123`

## Build

```bash
cd frontend
npm run build
```

## Padrao UX (FASE 14)

- Layout principal com sidebar agrupada por `Operacao` e `Administracao`, topbar com contexto de sessao, destaque de rota ativa e comportamento adaptado para telas menores.
- Formularios com labels sempre visiveis, foco visual consistente, mensagens de erro amigaveis e botoes padronizados.
- Tabelas administrativas e operacionais com cabecalho claro, badges centralizados, estados de loading/erro/vazio e paginacao uniforme.
- Badges compartilhados para status, prioridade, severidade, leitura de alerta e estados binarios simples.
- Confirmacao visual reutilizavel (`ConfirmDialog`) aplicada em acoes criticas de resolucao e fechamento.
- Mensagens operacionais padronizadas para sessao expirada, sem permissao, nao encontrado, limite de tentativas, upload invalido e erro inesperado.

## Relatorios (FASE 15)

- Menu `Relatorios` visivel apenas para `admin`, `director`, `engineering` e `manager`.
- Tipos disponiveis: `Chamados`, `Custos`, `SLA`, `Unidades` e `Fornecedores`.
- A tela reutiliza `PageHeader`, `FilterBar`, `StatCard`, `Table`, `Pagination`, `LoadingState`, `ErrorState`, `EmptyState`, `Button` e badges padronizados.
- Filtros visuais: periodo, unidade, regiao, status, categoria, prioridade, severidade, fornecedor, atraso e aprovacao.
- `manager` enxerga a propria unidade travada visualmente; o backend continua como validacao definitiva do escopo.
- A exportacao CSV usa o token no header `Authorization`, sem expor credenciais na URL.
- Erros de permissao, sessao expirada e limite de exportacao sao tratados com mensagens operacionais amigaveis.

## Limitacoes desta fase

- sem IA
- sem integracao externa
- sem biblioteca pesada de UI
- sem alteracao de regra critica no backend
- sem PDF
- sem Excel
- sem agendamento automatico

## Testes

- Validacao automatica disponivel nesta fase: `npm run build`
- Suite E2E minima disponivel em `frontend/e2e/login.spec.ts`

```bash
cd frontend
npm install
npm run build
npm run e2e
```

Observacoes de E2E:

- O teste usa Playwright com Chrome do sistema quando disponivel.
- O backend precisa estar ativo em `http://127.0.0.1:8000`.
- Se o navegador nao estiver instalado no ambiente, rode `npx playwright install chromium` ou ajuste o canal do browser.

## Testar login

1. Rode o backend com `alembic upgrade head`, `python scripts/seed_demo.py` e `uvicorn app.main:app --reload`.
2. Rode o frontend com `npm install` e `npm run dev`.
3. Abra `http://127.0.0.1:5173/login`.
4. Entre com `admin@local.test` / `admin123`.
5. Confirme o redirecionamento para `/dashboard`.

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

## Relatorios e exportacao CSV (FASE 15)

- API real consumida em `/reports/*`
- Download de `chamados.csv`, `custos.csv`, `sla.csv`, `unidades.csv` e `fornecedores.csv`
- Loading dedicado durante exportacao
- Tabela paginada, filtros aplicados por consulta e estados de vazio/erro
- Bloqueio amigavel quando o backend informa que o limite de `REPORT_EXPORT_MAX_ROWS` foi excedido

## Limitacoes preservadas

- sem Celery
- sem notificacoes
- sem IA
- sem storage externo
