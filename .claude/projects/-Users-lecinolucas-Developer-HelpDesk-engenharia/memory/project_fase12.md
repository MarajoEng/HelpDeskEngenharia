---
name: fase12-concluida
description: FASE 12 concluida — SLA e alertas assincronos com Celery, Redis, TicketAlert model, monitoramento sincronico e tela de alertas; 220 testes passando
metadata:
  type: project
---

FASE 12 entregue em 2026-06-25.

**Why:** Adicionar infraestrutura assincrona com Celery/Redis para monitorar SLA, identificar chamados atrasados e gerar alertas internos sem bloquear requisicoes.

**How to apply:** Worker Celery pode ser iniciado com `celery -A app.workers.celery_app.celery_app worker --loglevel=info`. FastAPI funciona mesmo sem worker ativo.

Arquivos criados/alterados:
- requirements.txt: celery, redis adicionados
- config.py: redis_url, celery_broker_url, celery_result_backend, sla_monitor_lookback_days, sla_alert_repeat_hours
- models/enums.py: AlertType, AlertSeverity
- models/ticket_alert.py: TicketAlert model (CreatedAtMixin)
- models/ticket.py: alerts relationship
- alembic/versions/0005_create_ticket_alerts.py
- app/workers/celery_app.py + tasks.py
- schemas/alert.py
- repositories/alert_repository.py
- services/alert_service.py (run_sla_monitoring sincrono)
- api/routes/alert_routes.py
- main.py: alert_router registrado
- tests/test_alert_fase12.py: 37 testes
- frontend: types/alert.ts, api/alertApi.ts, pages/AlertsPage.tsx
- App.tsx: /alerts route
- AppLayout.tsx: Alertas nav item
- DashboardPage.tsx: bloco de alertas criticos

220 testes passando (162 antes + 58 novos: 37 de alerta + 21 regressao).

[[fase6-concluida]]
