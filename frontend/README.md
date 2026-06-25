# Frontend

Base em React + TypeScript + Vite para o Portal de Chamados Engenharia, com autenticacao da FASE 3, cadastros administrativos da FASE 4 e abertura de chamados da FASE 5.

## Estrutura

- `src/App.tsx`: roteamento com protecao inicial de sessao.
- `src/hooks/useAuth.tsx`: contexto de autenticacao, token e logout.
- `src/api/authApi.ts`: integracao com `/auth/login` e `/auth/me`.
- `src/api/unitApi.ts`: integracao com `/units`.
- `src/api/userApi.ts`: integracao com `/users`.
- `src/api/ticketApi.ts`: integracao com `/tickets`.
- `src/pages/LoginPage.tsx`: tela de login.
- `src/pages/CreateTicketPage.tsx`: abertura de chamado.
- `src/pages/TicketsPage.tsx`: listagem paginada de chamados.
- `src/pages/TicketDetailPage.tsx`: detalhe simples do chamado.
- `src/pages/UnitsPage.tsx`: listagem e modal de criacao/edicao de unidades.
- `src/pages/UsersPage.tsx`: listagem e modal de criacao/edicao de usuarios.
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
4. Acesse `Chamados` para testar filtros e paginação.
5. Acesse `Abrir chamado` para criar um ticket real via `POST /tickets`.

## Permissoes desta fase

- `admin`, `engineering` e `director`: podem abrir e consultar chamados.
- `manager`: abre e consulta chamados apenas da propria unidade.
- `supplier`: nao acessa chamados nesta fase.

## Limitacoes desta fase

- sem triagem, aprovacao, execucao, encerramento ou comentarios;
- sem upload de anexos;
- sem dashboard e relatorios.
