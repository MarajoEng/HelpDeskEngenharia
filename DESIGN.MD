# DESIGN

- Identidade visual: linguagem corporativa, limpa e técnica, com contraste forte, tipografia legível e sem visual improvisado.
- Layout base: sidebar fixa para navegação principal e topbar para contexto, busca, filtros globais e ações rápidas.
- Páginas: sempre com título, subtítulo curto, bloco de ações e conteúdo organizado por seções previsíveis.
- Cards: usar cabeçalho curto, métrica ou contexto central, borda discreta e espaçamento consistente.
- Tabelas: priorizar leitura rápida, cabeçalho fixo quando necessário, filtros claros e estados de ordenação visíveis.
- Status: badges semânticos e consistentes para `open`, `in_progress`, `waiting_approval`, `resolved`, `closed` e derivados.
- Prioridade: badges distintos para `low`, `medium`, `high` e `critical`, com contraste suficiente sem depender só de cor.
- Formulários: labels visíveis, ajuda contextual curta, validação próxima ao campo e ações principais destacadas.
- Dashboard: números reais da API, recortes temporais explícitos e destaque para gargalos, SLA e fila operacional.
- Estados: toda tela deve prever loading, erro e vazio com mensagens objetivas e ações de recuperação quando fizer sentido.
- Regra final: proibido mock fixo em tela final ou indicador visual que simule dado real sem origem na API.
