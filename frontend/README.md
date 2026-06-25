# Frontend

React + TypeScript + Vite para o Portal de Chamados Engenharia com autenticacao (FASE 3), cadastros (FASE 4), abertura (FASE 5), listagem/detalhe avancado (FASE 6) e triagem tecnica da engenharia (FASE 7).

## Estrutura

- `src/App.tsx`: roteamento com protecao inicial de sessao.
- `src/hooks/useAuth.tsx`: contexto de autenticacao, token e logout.
- `src/api/authApi.ts`: integracao com `/auth/login` e `/auth/me`.
- `src/api/unitApi.ts`: integracao com `/units`.
- `src/api/userApi.ts`: integracao com `/users`.
- `src/api/ticketApi.ts`: integracao com `/tickets`.
- `src/pages/LoginPage.tsx`: tela de login.
- `src/pages/CreateTicketPage.tsx`: abertura de chamado.
- `src/pages/EngineeringQueuePage.tsx`: fila da engenharia com filtros, cards de resumo e acao de triagem.
- `src/pages/TicketsPage.tsx`: listagem paginada com filtros avancados (busca textual, only_late, bicos parados, custo min/max).
- `src/pages/TicketDetailPage.tsx`: detalhe completo com indicadores, historico em timeline e acao de triagem.
- `src/pages/UnitsPage.tsx`: listagem e modal de criacao/edicao de unidades.
- `src/pages/UsersPage.tsx`: listagem e modal de criacao/edicao de usuarios.
- `src/components/tickets/TriageTicketModal.tsx`: formulario/modal de triagem integrado ao backend real.
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
8. Clique em `Detalhe` para ver historico, indicadores e dados completos do chamado atualizados apos a triagem.

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

## Permissoes

- `admin`, `engineering` e `director`: abrem e consultam todos os chamados.
- `admin` e `engineering`: acessam a fila `Engenharia` e executam triagem.
- `manager`: restritos a chamados da propria unidade.
- `supplier`: sem acesso a chamados nesta fase.

## Limitacoes desta fase

- sem aprovacao, execucao, encerramento ou comentarios fora do fluxo de triagem;
- sem upload de anexos;
- sem dashboard e relatorios;
- sem Celery e sem fluxos da FASE 8 em diante.
