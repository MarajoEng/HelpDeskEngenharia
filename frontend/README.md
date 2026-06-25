# Frontend

React + TypeScript + Vite para o Portal de Chamados Engenharia com autenticacao (FASE 3), cadastros (FASE 4), abertura (FASE 5), listagem/detalhe avancado (FASE 6), triagem tecnica da engenharia (FASE 7) e aprovacao de orcamento por alcadas configuraveis (FASE 8).

## Estrutura

- `src/App.tsx`: roteamento com protecao inicial de sessao.
- `src/hooks/useAuth.tsx`: contexto de autenticacao, token e logout.
- `src/api/authApi.ts`: integracao com `/auth/login` e `/auth/me`.
- `src/api/unitApi.ts`: integracao com `/units`.
- `src/api/userApi.ts`: integracao com `/users`.
- `src/api/approvalLevelApi.ts`: integracao administrativa com `/approval-levels`.
- `src/api/ticketApi.ts`: integracao com `/tickets`.
- `src/pages/LoginPage.tsx`: tela de login.
- `src/pages/CreateTicketPage.tsx`: abertura de chamado.
- `src/pages/EngineeringQueuePage.tsx`: fila da engenharia com filtros, cards de resumo e acao de triagem.
- `src/pages/TicketsPage.tsx`: listagem paginada com filtros avancados (busca textual, only_late, bicos parados, custo min/max).
- `src/pages/TicketDetailPage.tsx`: detalhe completo com indicadores, historico em timeline e acao de triagem.
- `src/pages/ApprovalLevelsPage.tsx`: configuracao paginada de alcadas para `admin`.
- `src/pages/UnitsPage.tsx`: listagem e modal de criacao/edicao de unidades.
- `src/pages/UsersPage.tsx`: listagem e modal de criacao/edicao de usuarios.
- `src/components/tickets/TriageTicketModal.tsx`: formulario/modal de triagem integrado ao backend real.
- `src/components/tickets/RequestApprovalModal.tsx`: solicitacao de aprovacao de orcamento no detalhe.
- `src/components/tickets/ApprovalDecisionModal.tsx`: decisao de aprovacao ou reprovacao conforme a alcada pendente.
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
10. Acesse `Alcadas` como `admin` para criar, editar, filtrar e inativar niveis de aprovacao.

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
- `director` e demais roles configuradas em alcada ativa: podem decidir aprovacoes compativeis.
- `manager`: restritos a chamados da propria unidade.
- `supplier`: sem acesso a chamados nesta fase.

## Limitacoes desta fase

- sem execucao, encerramento ou comentarios fora do fluxo oficial de triagem/aprovacao;
- sem upload de anexos;
- sem dashboard e relatorios;
- sem Celery e sem fluxos da FASE 9 em diante.
