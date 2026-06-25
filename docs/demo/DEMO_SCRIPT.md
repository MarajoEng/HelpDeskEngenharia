# Roteiro de Demonstração (Demo Script)

**Duração Estimada**: 5 a 10 minutos.

Este roteiro guia a apresentação executiva do MVP do Portal de Chamados Engenharia, destacando a resolução das dores atuais da empresa.

## 1. Contexto e Problema Atual (1 min)

* **O Problema**: Atualmente, chamados são informais (WhatsApp/e-mail), gerando falta de rastreabilidade, perda de informações e aprovações lentas.
* **O Impacto**: Bicos de combustível parados geram perda de receita (lucro cessante). A Engenharia não tem uma fila centralizada de prioridades, e a Diretoria carece de visão macro dos custos.
* **A Solução**: O Portal de Chamados foi criado para ser a fonte única da verdade para a engenharia e manutenção estrutural de toda a rede de postos.

## 2. Visão da Diretoria (2 min)

* **Login**: Entre como `diretor@local.test` / `admin123`.
* **Ação**: Acesse o Dashboard.
* **Destaques**:
  * Mostre a visão geral executiva: quantidade de chamados críticos, custos estimados e custos aprovados na rede.
  * Mostre a métrica de "Bicos Parados" e o prejuízo diário estimado (perda financeira real).
  * Exiba os alertas críticos do sistema (SLA estourado). O diretor consegue ver onde estão os gargalos sem precisar ligar para ninguém.

## 3. Visão do Gerente (2 min)

* **Login**: Entre como `gerente0101@local.test` / `admin123`.
* **Ação**: Abra um novo chamado crítico.
* **Destaques**:
  * O gerente só enxerga a própria unidade (Posto 0101).
  * Vá em "Novo Chamado". Simule um vazamento de bomba (Categoria: `Bomba`, Prioridade: `Crítica`).
  * Mostre a marcação de bicos parados e o campo de perda estimada.
  * Salve o chamado. Mostre a rastreabilidade imediata (Histórico gravado com data e hora).

## 4. Visão da Engenharia (3 min)

* **Login**: Entre como `engenharia@local.test` / `admin123`.
* **Ação**: Triagem, Solicitação de Aprovação e Execução.
* **Destaques**:
  * Mostre a Fila da Engenharia. A engenharia tem visão total de todas as unidades, podendo priorizar o que é mais crítico.
  * Abra o chamado recém-criado pelo gerente.
  * Realize a triagem técnica (mudança de status para `Triage`), e indique que precisa de aprovação (`Waiting Approval`) devido ao alto custo.
  * Simule a vinculação de um Fornecedor e o andamento para `In Progress`.
  * Mostre como a engenharia pode encerrar um chamado, registrando a evidência (anexo final) e o custo final.

## 5. Visão do Diretor / Admin - Alçadas e Relatórios (1 min)

* **Login**: Entre novamente como `diretor@local.test` ou `admin@local.test`.
* **Ação**: Aprovação financeira e Relatórios.
* **Destaques**:
  * Mostre a aba de **Aprovações**. Aprove o orçamento do chamado anterior respeitando a tabela de alçadas configurada.
  * Vá na aba de **Relatórios** e mostre a tabela de dados, provando que é possível exportar tudo para **CSV** para análise em BI.
  * Demonstre rapidamente a tela de **Auditoria (Audit Logs)**, provando que o sistema é 100% compliance (todo acesso e clique crítico fica guardado).

## 6. Fechamento e Benefícios (1 min)

* **Resumo dos Ganhos**:
  * **Ganho de Controle**: Fim do "boca a boca". Cada passo tem responsável.
  * **Redução de Perdas**: Visibilidade imediata sobre lucro cessante com bicos parados, direcionando o esforço.
  * **Conformidade**: Auditoria automática e aprovação financeira travada por limites de alçada.
  * **Decisão baseada em dados**: A diretoria agora tem histórico de problemas recorrentes por posto.
* **Conclusão**: O MVP entrega controle de ponta a ponta. Está pronto para operação controlada.
