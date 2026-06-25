# Frontend

Base em React + TypeScript + Vite para o Portal de Chamados Engenharia, com autenticacao da FASE 3 e cadastro administrativo de unidades e usuarios da FASE 4.

## Estrutura

- `src/App.tsx`: roteamento com protecao inicial de sessao.
- `src/hooks/useAuth.tsx`: contexto de autenticacao, token e logout.
- `src/api/authApi.ts`: integracao com `/auth/login` e `/auth/me`.
- `src/api/unitApi.ts`: integracao com `/units`.
- `src/api/userApi.ts`: integracao com `/users`.
- `src/pages/LoginPage.tsx`: tela de login.
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

## Testar cadastros

1. Entre com um usuario `admin`.
2. Use a sidebar para acessar `Unidades` e `Usuarios`.
3. Valide filtros, paginacao e os modais de criacao/edicao consumindo a API real.
