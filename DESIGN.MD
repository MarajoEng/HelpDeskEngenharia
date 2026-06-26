---

name: Portal de Chamados Engenharia
version: 1.0.0
type: design-system
product: engineering-ticket-platform

colors:
primary:
value: "#0F172A"
role: "Cor principal para navegação, títulos fortes e estrutura institucional."
secondary:
value: "#1E40AF"
role: "Cor de ação principal para botões, links e elementos ativos."
success:
value: "#15803D"
role: "Usada para chamados concluídos, SLA cumprido e aprovações."
warning:
value: "#D97706"
role: "Usada para alertas, pendências e chamados próximos do vencimento."
danger:
value: "#B91C1C"
role: "Usada para chamados críticos, SLA estourado, reprovação e risco operacional."
background:
value: "#F8FAFC"
role: "Fundo geral das telas."
surface:
value: "#FFFFFF"
role: "Cards, tabelas, modais e painéis."
border:
value: "#E2E8F0"
role: "Bordas leves e separadores."
text:
value: "#0F172A"
role: "Texto principal."
muted:
value: "#64748B"
role: "Textos secundários e descrições."

typography:
fontFamily:
value: "Inter, system-ui, sans-serif"
headingWeight:
value: 700
bodyWeight:
value: 400

spacing:
xs:
value: "4px"
sm:
value: "8px"
md:
value: "16px"
lg:
value: "24px"
xl:
value: "32px"

radius:
sm:
value: "6px"
md:
value: "10px"
lg:
value: "16px"

layout:
maxContentWidth:
value: "1440px"
sidebarWidth:
value: "260px"
topbarHeight:
value: "64px"
-------------

# DESIGN.md — Portal de Chamados Engenharia

## Identidade visual

O sistema deve transmitir controle, rastreabilidade, engenharia, operação e tomada de decisão.

A interface deve parecer profissional, limpa e executiva.
Evitar aparência infantil, colorida demais ou genérica.

Priorizar:

* clareza;
* dados visíveis;
* status bem destacados;
* tabelas organizadas;
* dashboards objetivos;
* telas operacionais rápidas;
* hierarquia visual forte;
* baixo ruído visual.

## Layout principal

O sistema deve usar layout administrativo com:

* sidebar lateral para navegação;
* topbar superior com usuário, unidade e ações rápidas;
* conteúdo central em cards;
* largura confortável para dashboards e tabelas;
* responsividade para notebook e desktop.

Menu lateral sugerido:

* Dashboard;
* Chamados;
* Abrir chamado;
* Engenharia;
* Aprovações;
* Unidades;
* Usuários;
* Relatórios;
* Configurações.

## Padrão de páginas

Toda página deve seguir a estrutura:

1. Título da página;
2. Descrição curta;
3. Ações principais no topo;
4. Filtros quando necessário;
5. Conteúdo em cards ou tabela;
6. Estados de loading, vazio e erro.

Exemplo:

Título: Chamados
Descrição: Acompanhe os chamados críticos da rede.
Ação: Novo chamado
Filtros: unidade, status, prioridade, categoria e período.
Conteúdo: tabela paginada.

## Cards

Cards devem ser usados para indicadores, resumo de chamados e blocos de informação.

Padrão:

* fundo branco;
* borda leve;
* raio médio;
* sombra sutil;
* título pequeno;
* número principal grande;
* descrição curta;
* indicador de variação quando existir.

Cards críticos podem usar borda ou ícone em vermelho, mas não devem poluir a tela.

## Tabelas

Tabelas são essenciais no sistema.

Regras:

* nunca carregar lista sem paginação;
* colunas claras;
* status com badge;
* prioridade com badge;
* data formatada;
* ação principal sempre visível;
* filtros acima da tabela;
* ordenação quando fizer sentido;
* empty state quando não houver dados.

Tabela de chamados deve exibir:

* número;
* unidade;
* categoria;
* prioridade;
* status;
* aberto em;
* SLA;
* responsável;
* ação de detalhes.

## Badges de status

Status devem ter cores consistentes:

* Aberto: cinza/azul;
* Em triagem: azul;
* Aguardando aprovação: amarelo;
* Aprovado: verde;
* Reprovado: vermelho;
* Em execução: azul forte;
* Aguardando fornecedor: laranja;
* Aguardando unidade: amarelo;
* Resolvido: verde;
* Encerrado: verde escuro;
* Cancelado: cinza.

## Prioridade

Prioridades:

* Baixa: cinza;
* Média: azul;
* Alta: laranja;
* Crítica: vermelho.

Chamado crítico deve ser visualmente evidente, mas sem quebrar o layout.

## Formulários

Formulários devem ser claros e guiados.

Regras:

* labels sempre visíveis;
* mensagens de erro próximas ao campo;
* campos obrigatórios marcados;
* botões com ação clara;
* confirmação para ações críticas;
* validação no frontend e backend;
* textos simples para usuários operacionais.

Formulário de abertura de chamado deve priorizar:

* unidade;
* categoria;
* tipo do problema;
* título;
* descrição;
* prioridade percebida;
* impacto operacional;
* quantidade de bicos parados;
* evidências/fotos.

## Dashboard

Dashboard da diretoria deve ser executivo e objetivo.

Indicadores principais:

* chamados abertos;
* chamados críticos;
* chamados atrasados;
* bicos parados;
* perda estimada;
* custo aprovado;
* tempo médio de resolução;
* SLA geral.

Dashboard da engenharia deve ser operacional.

Indicadores principais:

* fila de triagem;
* aguardando aprovação;
* em execução;
* atrasados;
* vencendo hoje;
* aguardando fornecedor.

## Tela de detalhe do chamado

A tela de detalhe deve ter:

* cabeçalho com número, status e prioridade;
* dados da unidade;
* descrição do problema;
* impacto operacional;
* datas principais;
* SLA;
* anexos;
* histórico;
* aprovações;
* comentários;
* ações permitidas por perfil.

A timeline/histórico deve ser clara e mostrar quem fez cada ação e quando.

## Estados de tela

Toda tela deve tratar:

* loading;
* erro;
* vazio;
* sem permissão;
* sucesso;
* confirmação de ação crítica.

Nada deve falhar silenciosamente.

## Tom de texto

Usar linguagem profissional, simples e operacional.

Evitar termos técnicos para gerentes de posto.

Exemplos bons:

* “Chamado aberto com sucesso.”
* “Aguardando análise da engenharia.”
* “Anexe uma foto para comprovar a conclusão.”
* “Este chamado está com SLA vencido.”

Evitar:

* “Payload enviado.”
* “Mutation failed.”
* “Erro 500.”
* “Undefined status.”

## Regras de consistência

* Não criar estilos diferentes para cada tela.
* Não inventar novas cores fora dos tokens sem necessidade.
* Não usar componentes soltos quando já existir padrão.
* Não esconder informação crítica.
* Não usar mock fixo em tela final.
* Não encerrar chamado sem evidência.
* Não alterar status sem confirmação quando a ação for crítica.
* Não mostrar números de dashboard sem fonte real da API.
