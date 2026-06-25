# Checklist de Validação Pré-Demonstração

Siga este checklist rigorosamente antes de entrar na sala de reunião com a diretoria para garantir que tudo funcionará perfeitamente.

## 1. Ambiente e Dados

- [ ] O backend sobe sem erros (`uvicorn app.main:app --reload`).
- [ ] O frontend sobe sem erros (`npm run dev`).
- [ ] O banco de dados está rodando.
- [ ] As migrations estão na versão mais recente (`alembic upgrade head` sem erros).
- [ ] O script de seed roda com sucesso e populariza a base (`python scripts/seed_demo.py`).
- [ ] O script de seed é seguro e aborta automaticamente caso a variável ambiente `APP_ENV` seja `production`.

## 2. Acesso e Perfis

- [ ] O login de **Admin** funciona (`admin@local.test` / `admin123`).
- [ ] O login de **Gerente** funciona (`gerente0101@local.test` / `admin123`) e visualiza apenas a própria unidade.
- [ ] O login de **Engenharia** funciona (`engenharia@local.test` / `admin123`) e visualiza a fila consolidada.
- [ ] A caixa de "Credenciais Demo" é exibida apenas na tela de login de desenvolvimento.

## 3. Navegação e Dados Iniciais

- [ ] A tela inicial redireciona corretamente para o Dashboard.
- [ ] O **Dashboard** carrega corretamente com gráficos de barras e rankings utilizando os dados do seed.
- [ ] Os estados vazios do sistema são amigáveis e apresentam mensagens de orientação.

## 4. Fluxo do Chamado (Ponta a Ponta)

- [ ] A funcionalidade **Abrir Chamado** funciona e gera um `ticket_number` na base de dados.
- [ ] O gerente consegue ver o chamado que acabou de abrir.
- [ ] A **Triagem** feita pela Engenharia funciona, refletindo o novo status imediatamente.
- [ ] É possível solicitar **Aprovação** financeira para o chamado, passando a requisição para o nível correspondente.
- [ ] A **Execução** do chamado (passagem para status *In Progress* / *Waiting Supplier*) funciona.
- [ ] A **Resolução/Fechamento** do chamado funciona, registrando anexos (evidência) e os custos finais.

## 5. Auditoria e Relatórios

- [ ] **Alertas**: Alertas (SLA vencido, etc.) são devidamente gerados e visíveis.
- [ ] **Relatórios**: A tela de relatórios renderiza tabelas reais e os filtros aplicam alterações imediatas.
- [ ] A exportação de **CSV** baixa o arquivo corretamente.
- [ ] A **Auditoria (Audit Logs)** registra todas as ações críticas (criação de chamado, triagem, alteração de usuários e acessos).
