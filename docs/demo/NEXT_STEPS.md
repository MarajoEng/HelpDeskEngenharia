# Próximos Passos (Pós-Demo Executiva)

Após o sucesso do MVP e do alinhamento executivo, sugerem-se as seguintes fases subsequentes visando amadurecimento e operação escalável:

## 1. Deploy e Infraestrutura Nuvem
- **Storage Externo**: Migração do serviço de anexos local (`/uploads`) para AWS S3 ou equivalente, garantindo redundância, segurança e escalabilidade dos arquivos.
- **Deploy em Homologação**: Subida da stack completa para um ambiente cloud usando contêineres e um banco gerenciado.
- **CI/CD Pipeline**: Automação de builds e testes no GitHub Actions.

## 2. Experiência e Comunicação
- **Notificações Automáticas e E-mail**: Integração com ferramentas como SendGrid ou AWS SES para enviar resumo da triagem para os gerentes e pedidos de aprovação à diretoria via e-mail.
- **Integração com WhatsApp**: Emitir notificações via API de WhatsApp Business sobre a resolução ou agravamento (Alertas) do chamado para comunicação imediata, especialmente para tickets de criticidade alta.
- **PWA e App Mobile**: Transformar o React Vite num Progressive Web App completo para os gerentes de pista abrirem os chamados diretamente do pátio utilizando o celular.

## 3. Integração de Processos
- **Portal do Fornecedor (Supplier)**: Ativar o nível de acesso "Supplier", fornecendo uma tela simples onde fornecedores podem anexar faturas, responder aos chamados delegados a eles e notificar conclusão física do serviço.
- **Sincronização ERP**: Integração via API ao Protheus ou TOTVS local para:
  - Exportar/Sincronizar as Unidades e Fornecedores mantendo a tabela-base viva;
  - Extrair o rateio financeiro para criar automaticamente a ordem de compra/pagamento ao fechar o chamado com o custo final.

## 4. BI Avançado
- **Data Lake Integration**: Exportar dados consolidados ou liberar view de leitura segura em banco espelhado para ferramentas como Power BI, Metabase ou Tableau, cruzando métricas financeiras dos postos com os custos de manutenção da engenharia.
- **Métricas Compostas**: Mapear tempo médio de reparo (MTTR) e custo total de propriedade por categoria de equipamento (ex: custo histórico para manter Bombas na regional SP).

## 5. Autenticação Corporativa
- **SSO (Single Sign-On)**: Implementar Microsoft Entra ID (Azure AD), Google Workspace ou Okta na autenticação do portal para não gerenciar senhas e remover acessos de usuários inativados instantaneamente via política corporativa.
