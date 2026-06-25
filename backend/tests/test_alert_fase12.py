"""FASE 12 — testes de SLA e alertas assincronos."""
from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from app.models.enums import AlertSeverity, AlertType, TicketStatus, UserRole
from app.models.ticket import Ticket
from app.models.ticket_alert import TicketAlert


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _create_ticket(
    db_session,
    *,
    unit_id: int,
    opened_by_user_id: int,
    ticket_number: str,
    status: TicketStatus,
    sla_due_at: datetime | None = None,
    expected_resolution_at: datetime | None = None,
    opened_at: datetime | None = None,
    started_at: datetime | None = None,
) -> Ticket:
    now = datetime.now(UTC)
    ticket = Ticket(
        ticket_number=ticket_number,
        unit_id=unit_id,
        opened_by_user_id=opened_by_user_id,
        category="fuel_pump",
        problem_type="Falha operacional",
        title=f"Chamado {ticket_number}",
        description="Descricao do chamado",
        priority="medium",
        severity="medium",
        status=status,
        requires_approval=False,
        opened_at=opened_at or now,
        started_at=started_at,
        sla_due_at=sla_due_at,
        expected_resolution_at=expected_resolution_at,
    )
    db_session.add(ticket)
    db_session.commit()
    db_session.refresh(ticket)
    return ticket


def _create_alert(
    db_session,
    *,
    ticket_id: int,
    alert_type: AlertType,
    severity: AlertSeverity = AlertSeverity.WARNING,
    message: str = "Alerta de teste",
    is_read: bool = False,
    created_at: datetime | None = None,
) -> TicketAlert:
    alert = TicketAlert(
        ticket_id=ticket_id,
        alert_type=alert_type,
        severity=severity,
        message=message,
        is_read=is_read,
    )
    db_session.add(alert)
    db_session.commit()
    if created_at is not None:
        alert.created_at = created_at
        db_session.add(alert)
        db_session.commit()
    db_session.refresh(alert)
    return alert


# ---------------------------------------------------------------------------
# Infra / config
# ---------------------------------------------------------------------------


def test_celery_app_imports_without_error() -> None:
    from app.workers.celery_app import celery_app

    assert celery_app is not None
    assert celery_app.main == "helpdesk_engenharia"


def test_celery_app_has_monitor_task() -> None:
    from app.workers.celery_app import celery_app
    import app.workers.tasks  # noqa: F401 — trigger registration

    assert "app.workers.tasks.monitor_sla_alerts" in celery_app.tasks


def test_settings_has_redis_url() -> None:
    from app.core.config import get_settings

    settings = get_settings()
    assert hasattr(settings, "redis_url")
    assert "redis" in settings.redis_url or "redis" in settings.celery_broker_url


def test_settings_has_sla_monitor_params() -> None:
    from app.core.config import get_settings

    settings = get_settings()
    assert settings.sla_monitor_lookback_days > 0
    assert settings.sla_alert_repeat_hours > 0


@pytest.mark.anyio
async def test_fastapi_still_healthy_after_fase12(client) -> None:
    response = await client.get("/health/live")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


# ---------------------------------------------------------------------------
# SLA monitoring logic (synchronous, no Celery needed)
# ---------------------------------------------------------------------------


def test_creates_sla_late_alert(db_session, create_unit, create_user) -> None:
    from app.services.alert_service import run_sla_monitoring

    unit = create_unit(code="U-SLA-01", name="Unidade SLA")
    user = create_user(email="admin-sla@local.test", role=UserRole.ADMIN)
    now = datetime.now(UTC)

    ticket = _create_ticket(
        db_session,
        unit_id=unit.id,
        opened_by_user_id=user.id,
        ticket_number="SLA-001",
        status=TicketStatus.OPEN,
        sla_due_at=now - timedelta(hours=2),
    )

    result = run_sla_monitoring(db_session)

    assert result["created_alerts"] == 1
    assert result["checked_tickets"] >= 1
    db_session.commit()

    alert = db_session.query(TicketAlert).filter_by(ticket_id=ticket.id).first()
    assert alert is not None
    assert alert.alert_type == AlertType.SLA_LATE
    assert alert.severity == AlertSeverity.CRITICAL


def test_creates_sla_due_soon_alert(db_session, create_unit, create_user) -> None:
    from app.services.alert_service import run_sla_monitoring

    unit = create_unit(code="U-SLA-02", name="Unidade SLA Due Soon")
    user = create_user(email="admin-sla2@local.test", role=UserRole.ADMIN)
    now = datetime.now(UTC)

    ticket = _create_ticket(
        db_session,
        unit_id=unit.id,
        opened_by_user_id=user.id,
        ticket_number="SLA-002",
        status=TicketStatus.TRIAGE,
        sla_due_at=now + timedelta(hours=12),
    )

    result = run_sla_monitoring(db_session)

    assert result["created_alerts"] == 1
    db_session.commit()

    alert = db_session.query(TicketAlert).filter_by(ticket_id=ticket.id).first()
    assert alert is not None
    assert alert.alert_type == AlertType.SLA_DUE_SOON
    assert alert.severity == AlertSeverity.WARNING


def test_creates_execution_late_alert(db_session, create_unit, create_user) -> None:
    from app.services.alert_service import run_sla_monitoring

    unit = create_unit(code="U-SLA-03", name="Unidade Exec Late")
    user = create_user(email="eng-sla@local.test", role=UserRole.ENGINEERING)
    now = datetime.now(UTC)

    ticket = _create_ticket(
        db_session,
        unit_id=unit.id,
        opened_by_user_id=user.id,
        ticket_number="SLA-003",
        status=TicketStatus.IN_PROGRESS,
        started_at=now - timedelta(hours=4),
        expected_resolution_at=now - timedelta(hours=1),
    )

    result = run_sla_monitoring(db_session)

    assert result["created_alerts"] == 1
    db_session.commit()

    alert = db_session.query(TicketAlert).filter_by(ticket_id=ticket.id).first()
    assert alert is not None
    assert alert.alert_type == AlertType.EXECUTION_LATE


def test_no_alert_for_resolved_ticket(db_session, create_unit, create_user) -> None:
    from app.services.alert_service import run_sla_monitoring

    unit = create_unit(code="U-SLA-04", name="Unidade Resolvida")
    user = create_user(email="eng-sla2@local.test", role=UserRole.ENGINEERING)
    now = datetime.now(UTC)

    _create_ticket(
        db_session,
        unit_id=unit.id,
        opened_by_user_id=user.id,
        ticket_number="SLA-004",
        status=TicketStatus.RESOLVED,
        sla_due_at=now - timedelta(hours=1),
    )

    result = run_sla_monitoring(db_session)
    assert result["created_alerts"] == 0


def test_no_alert_for_closed_ticket(db_session, create_unit, create_user) -> None:
    from app.services.alert_service import run_sla_monitoring

    unit = create_unit(code="U-SLA-05", name="Unidade Fechada")
    user = create_user(email="eng-sla3@local.test", role=UserRole.ENGINEERING)
    now = datetime.now(UTC)

    _create_ticket(
        db_session,
        unit_id=unit.id,
        opened_by_user_id=user.id,
        ticket_number="SLA-005",
        status=TicketStatus.CLOSED,
        sla_due_at=now - timedelta(hours=1),
    )

    result = run_sla_monitoring(db_session)
    assert result["created_alerts"] == 0


def test_no_alert_for_canceled_ticket(db_session, create_unit, create_user) -> None:
    from app.services.alert_service import run_sla_monitoring

    unit = create_unit(code="U-SLA-06", name="Unidade Cancelada")
    user = create_user(email="eng-sla4@local.test", role=UserRole.ENGINEERING)
    now = datetime.now(UTC)

    _create_ticket(
        db_session,
        unit_id=unit.id,
        opened_by_user_id=user.id,
        ticket_number="SLA-006",
        status=TicketStatus.CANCELED,
        sla_due_at=now - timedelta(hours=1),
    )

    result = run_sla_monitoring(db_session)
    assert result["created_alerts"] == 0


def test_no_alert_without_sla_due_at(db_session, create_unit, create_user) -> None:
    from app.services.alert_service import run_sla_monitoring

    unit = create_unit(code="U-SLA-07", name="Unidade Sem SLA")
    user = create_user(email="eng-sla5@local.test", role=UserRole.ENGINEERING)

    _create_ticket(
        db_session,
        unit_id=unit.id,
        opened_by_user_id=user.id,
        ticket_number="SLA-007",
        status=TicketStatus.OPEN,
        sla_due_at=None,
    )

    result = run_sla_monitoring(db_session)
    assert result["created_alerts"] == 0


def test_does_not_duplicate_recent_alert(db_session, create_unit, create_user) -> None:
    from app.services.alert_service import run_sla_monitoring

    unit = create_unit(code="U-SLA-08", name="Unidade Dedup")
    user = create_user(email="admin-sla3@local.test", role=UserRole.ADMIN)
    now = datetime.now(UTC)

    ticket = _create_ticket(
        db_session,
        unit_id=unit.id,
        opened_by_user_id=user.id,
        ticket_number="SLA-008",
        status=TicketStatus.OPEN,
        sla_due_at=now - timedelta(hours=2),
    )

    # First run: creates alert
    run_sla_monitoring(db_session)
    db_session.commit()

    # Second run: same ticket still late, within repeat window → skips
    result2 = run_sla_monitoring(db_session)
    assert result2["created_alerts"] == 0
    assert result2["skipped_duplicates"] >= 1


def test_creates_alert_after_repeat_hours_window(db_session, create_unit, create_user) -> None:
    from app.services.alert_service import run_sla_monitoring
    from app.core.config import get_settings

    settings = get_settings()
    unit = create_unit(code="U-SLA-09", name="Unidade Repeat")
    user = create_user(email="admin-sla4@local.test", role=UserRole.ADMIN)
    now = datetime.now(UTC)

    ticket = _create_ticket(
        db_session,
        unit_id=unit.id,
        opened_by_user_id=user.id,
        ticket_number="SLA-009",
        status=TicketStatus.OPEN,
        sla_due_at=now - timedelta(hours=2),
    )

    # Create an old alert (beyond repeat window)
    old_alert = TicketAlert(
        ticket_id=ticket.id,
        alert_type=AlertType.SLA_LATE,
        severity=AlertSeverity.CRITICAL,
        message="Alerta antigo",
    )
    db_session.add(old_alert)
    db_session.commit()
    old_alert.created_at = now - timedelta(hours=settings.sla_alert_repeat_hours + 1)
    db_session.add(old_alert)
    db_session.commit()

    result = run_sla_monitoring(db_session)
    assert result["created_alerts"] == 1


def test_sla_due_after_24h_does_not_create_due_soon(db_session, create_unit, create_user) -> None:
    from app.services.alert_service import run_sla_monitoring

    unit = create_unit(code="U-SLA-10", name="Unidade SLA Far")
    user = create_user(email="admin-sla5@local.test", role=UserRole.ADMIN)
    now = datetime.now(UTC)

    _create_ticket(
        db_session,
        unit_id=unit.id,
        opened_by_user_id=user.id,
        ticket_number="SLA-010",
        status=TicketStatus.OPEN,
        sla_due_at=now + timedelta(hours=30),
    )

    result = run_sla_monitoring(db_session)
    assert result["created_alerts"] == 0


# ---------------------------------------------------------------------------
# Alert list — permissions
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_admin_lists_alerts(client, db_session, create_unit, create_user, auth_header_for_user) -> None:
    unit = create_unit(code="U-ALERT-01", name="Unidade Alerts")
    admin = create_user(email="admin-alert@local.test", role=UserRole.ADMIN)
    now = datetime.now(UTC)

    ticket = _create_ticket(
        db_session,
        unit_id=unit.id,
        opened_by_user_id=admin.id,
        ticket_number="ALERT-001",
        status=TicketStatus.OPEN,
        sla_due_at=now - timedelta(hours=1),
    )
    _create_alert(db_session, ticket_id=ticket.id, alert_type=AlertType.SLA_LATE, severity=AlertSeverity.CRITICAL)

    response = await client.get("/alerts", headers=auth_header_for_user(admin))
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    alert = data["items"][0]
    assert alert["alert_type"] == "sla_late"
    assert alert["ticket_number"] == "ALERT-001"


@pytest.mark.anyio
async def test_engineering_lists_alerts(client, db_session, create_unit, create_user, auth_header_for_user) -> None:
    unit = create_unit(code="U-ALERT-02", name="Unidade Eng Alerts")
    admin = create_user(email="admin-alert2@local.test", role=UserRole.ADMIN)
    eng = create_user(email="eng-alert@local.test", role=UserRole.ENGINEERING)
    now = datetime.now(UTC)

    ticket = _create_ticket(
        db_session,
        unit_id=unit.id,
        opened_by_user_id=admin.id,
        ticket_number="ALERT-002",
        status=TicketStatus.OPEN,
        sla_due_at=now - timedelta(hours=1),
    )
    _create_alert(db_session, ticket_id=ticket.id, alert_type=AlertType.SLA_LATE)

    response = await client.get("/alerts", headers=auth_header_for_user(eng))
    assert response.status_code == 200
    assert response.json()["total"] >= 1


@pytest.mark.anyio
async def test_director_lists_alerts(client, db_session, create_unit, create_user, auth_header_for_user) -> None:
    unit = create_unit(code="U-ALERT-03", name="Unidade Dir Alerts")
    admin = create_user(email="admin-alert3@local.test", role=UserRole.ADMIN)
    director = create_user(email="dir-alert@local.test", role=UserRole.DIRECTOR)
    now = datetime.now(UTC)

    ticket = _create_ticket(
        db_session,
        unit_id=unit.id,
        opened_by_user_id=admin.id,
        ticket_number="ALERT-003",
        status=TicketStatus.OPEN,
        sla_due_at=now - timedelta(hours=1),
    )
    _create_alert(db_session, ticket_id=ticket.id, alert_type=AlertType.SLA_LATE)

    response = await client.get("/alerts", headers=auth_header_for_user(director))
    assert response.status_code == 200
    assert response.json()["total"] >= 1


@pytest.mark.anyio
async def test_manager_lists_only_own_unit_alerts(
    client, db_session, create_unit, create_user, auth_header_for_user
) -> None:
    unit_a = create_unit(code="U-MGR-A", name="Unidade Manager A")
    unit_b = create_unit(code="U-MGR-B", name="Unidade Manager B")
    admin = create_user(email="admin-mgr@local.test", role=UserRole.ADMIN)
    manager = create_user(email="mgr-alert@local.test", role=UserRole.MANAGER, unit_id=unit_a.id)
    now = datetime.now(UTC)

    ticket_a = _create_ticket(
        db_session,
        unit_id=unit_a.id,
        opened_by_user_id=admin.id,
        ticket_number="ALERT-MGR-A",
        status=TicketStatus.OPEN,
        sla_due_at=now - timedelta(hours=1),
    )
    ticket_b = _create_ticket(
        db_session,
        unit_id=unit_b.id,
        opened_by_user_id=admin.id,
        ticket_number="ALERT-MGR-B",
        status=TicketStatus.OPEN,
        sla_due_at=now - timedelta(hours=1),
    )
    _create_alert(db_session, ticket_id=ticket_a.id, alert_type=AlertType.SLA_LATE)
    _create_alert(db_session, ticket_id=ticket_b.id, alert_type=AlertType.SLA_LATE)

    response = await client.get("/alerts", headers=auth_header_for_user(manager))
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["ticket_number"] == "ALERT-MGR-A"


@pytest.mark.anyio
async def test_supplier_cannot_list_alerts(
    client, db_session, create_unit, create_user, auth_header_for_user
) -> None:
    supplier = create_user(email="sup-alert@local.test", role=UserRole.SUPPLIER)
    response = await client.get("/alerts", headers=auth_header_for_user(supplier))
    assert response.status_code == 403


# ---------------------------------------------------------------------------
# Alert list — filters
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_filter_alerts_by_is_read(
    client, db_session, create_unit, create_user, auth_header_for_user
) -> None:
    unit = create_unit(code="U-FILT-01", name="Unidade Filtros")
    admin = create_user(email="admin-filt@local.test", role=UserRole.ADMIN)
    now = datetime.now(UTC)

    ticket = _create_ticket(
        db_session,
        unit_id=unit.id,
        opened_by_user_id=admin.id,
        ticket_number="FILT-001",
        status=TicketStatus.OPEN,
        sla_due_at=now - timedelta(hours=1),
    )
    _create_alert(db_session, ticket_id=ticket.id, alert_type=AlertType.SLA_LATE, is_read=False)
    _create_alert(db_session, ticket_id=ticket.id, alert_type=AlertType.SLA_LATE, is_read=True)

    headers = auth_header_for_user(admin)

    resp_unread = await client.get("/alerts?is_read=false", headers=headers)
    assert resp_unread.json()["total"] == 1

    resp_read = await client.get("/alerts?is_read=true", headers=headers)
    assert resp_read.json()["total"] == 1


@pytest.mark.anyio
async def test_filter_alerts_by_alert_type(
    client, db_session, create_unit, create_user, auth_header_for_user
) -> None:
    unit = create_unit(code="U-FILT-02", name="Unidade Tipo Filtro")
    admin = create_user(email="admin-filt2@local.test", role=UserRole.ADMIN)
    now = datetime.now(UTC)

    ticket = _create_ticket(
        db_session,
        unit_id=unit.id,
        opened_by_user_id=admin.id,
        ticket_number="FILT-002",
        status=TicketStatus.IN_PROGRESS,
        sla_due_at=now - timedelta(hours=1),
        expected_resolution_at=now - timedelta(hours=1),
        started_at=now - timedelta(hours=3),
    )
    _create_alert(db_session, ticket_id=ticket.id, alert_type=AlertType.SLA_LATE)
    _create_alert(db_session, ticket_id=ticket.id, alert_type=AlertType.EXECUTION_LATE)

    headers = auth_header_for_user(admin)

    resp = await client.get("/alerts?alert_type=sla_late", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert data["items"][0]["alert_type"] == "sla_late"


@pytest.mark.anyio
async def test_filter_alerts_by_severity(
    client, db_session, create_unit, create_user, auth_header_for_user
) -> None:
    unit = create_unit(code="U-FILT-03", name="Unidade Severity Filtro")
    admin = create_user(email="admin-filt3@local.test", role=UserRole.ADMIN)
    now = datetime.now(UTC)

    ticket = _create_ticket(
        db_session,
        unit_id=unit.id,
        opened_by_user_id=admin.id,
        ticket_number="FILT-003",
        status=TicketStatus.OPEN,
        sla_due_at=now - timedelta(hours=1),
    )
    _create_alert(db_session, ticket_id=ticket.id, alert_type=AlertType.SLA_LATE, severity=AlertSeverity.CRITICAL)
    _create_alert(db_session, ticket_id=ticket.id, alert_type=AlertType.SLA_DUE_SOON, severity=AlertSeverity.WARNING)

    headers = auth_header_for_user(admin)

    resp = await client.get("/alerts?severity=critical", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["total"] == 1
    assert resp.json()["items"][0]["severity"] == "critical"


# ---------------------------------------------------------------------------
# Mark alert as read
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_mark_alert_read(client, db_session, create_unit, create_user, auth_header_for_user) -> None:
    unit = create_unit(code="U-READ-01", name="Unidade Read")
    admin = create_user(email="admin-read@local.test", role=UserRole.ADMIN)
    now = datetime.now(UTC)

    ticket = _create_ticket(
        db_session,
        unit_id=unit.id,
        opened_by_user_id=admin.id,
        ticket_number="READ-001",
        status=TicketStatus.OPEN,
        sla_due_at=now - timedelta(hours=1),
    )
    alert = _create_alert(db_session, ticket_id=ticket.id, alert_type=AlertType.SLA_LATE)
    assert not alert.is_read

    response = await client.patch(f"/alerts/{alert.id}/read", headers=auth_header_for_user(admin))
    assert response.status_code == 200
    data = response.json()
    assert data["is_read"] is True
    assert data["read_at"] is not None


@pytest.mark.anyio
async def test_mark_alert_read_wrong_unit_as_manager(
    client, db_session, create_unit, create_user, auth_header_for_user
) -> None:
    unit_a = create_unit(code="U-READ-A", name="Unidade A")
    unit_b = create_unit(code="U-READ-B", name="Unidade B")
    admin = create_user(email="admin-read2@local.test", role=UserRole.ADMIN)
    manager = create_user(email="mgr-read@local.test", role=UserRole.MANAGER, unit_id=unit_a.id)
    now = datetime.now(UTC)

    ticket_b = _create_ticket(
        db_session,
        unit_id=unit_b.id,
        opened_by_user_id=admin.id,
        ticket_number="READ-WRONG",
        status=TicketStatus.OPEN,
        sla_due_at=now - timedelta(hours=1),
    )
    alert_b = _create_alert(db_session, ticket_id=ticket_b.id, alert_type=AlertType.SLA_LATE)

    response = await client.patch(f"/alerts/{alert_b.id}/read", headers=auth_header_for_user(manager))
    assert response.status_code == 403


@pytest.mark.anyio
async def test_mark_alert_read_not_found(client, create_user, auth_header_for_user) -> None:
    admin = create_user(email="admin-read3@local.test", role=UserRole.ADMIN)
    response = await client.patch("/alerts/999999/read", headers=auth_header_for_user(admin))
    assert response.status_code == 404


@pytest.mark.anyio
async def test_supplier_cannot_mark_alert_read(client, create_user, auth_header_for_user) -> None:
    supplier = create_user(email="sup-read@local.test", role=UserRole.SUPPLIER)
    response = await client.patch("/alerts/1/read", headers=auth_header_for_user(supplier))
    assert response.status_code == 403


# ---------------------------------------------------------------------------
# Mark all alerts as read
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_mark_all_alerts_read(
    client, db_session, create_unit, create_user, auth_header_for_user
) -> None:
    unit = create_unit(code="U-READALL-01", name="Unidade ReadAll")
    admin = create_user(email="admin-readall@local.test", role=UserRole.ADMIN)
    now = datetime.now(UTC)

    ticket = _create_ticket(
        db_session,
        unit_id=unit.id,
        opened_by_user_id=admin.id,
        ticket_number="READALL-001",
        status=TicketStatus.OPEN,
        sla_due_at=now - timedelta(hours=1),
    )
    _create_alert(db_session, ticket_id=ticket.id, alert_type=AlertType.SLA_LATE)
    _create_alert(db_session, ticket_id=ticket.id, alert_type=AlertType.SLA_DUE_SOON)

    response = await client.patch("/alerts/read-all", headers=auth_header_for_user(admin))
    assert response.status_code == 200
    data = response.json()
    assert data["marked_read"] == 2


@pytest.mark.anyio
async def test_supplier_cannot_mark_all_read(client, create_user, auth_header_for_user) -> None:
    supplier = create_user(email="sup-readall@local.test", role=UserRole.SUPPLIER)
    response = await client.patch("/alerts/read-all", headers=auth_header_for_user(supplier))
    assert response.status_code == 403


# ---------------------------------------------------------------------------
# run-sla-monitor endpoint
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_run_sla_monitor_admin_ok(
    client, db_session, create_unit, create_user, auth_header_for_user
) -> None:
    unit = create_unit(code="U-MON-01", name="Unidade Monitor")
    admin = create_user(email="admin-mon@local.test", role=UserRole.ADMIN)
    now = datetime.now(UTC)

    _create_ticket(
        db_session,
        unit_id=unit.id,
        opened_by_user_id=admin.id,
        ticket_number="MON-001",
        status=TicketStatus.OPEN,
        sla_due_at=now - timedelta(hours=3),
    )

    response = await client.post("/alerts/run-sla-monitor", headers=auth_header_for_user(admin))
    assert response.status_code == 200
    data = response.json()
    assert "checked_tickets" in data
    assert "created_alerts" in data
    assert "skipped_duplicates" in data
    assert data["created_alerts"] >= 1


@pytest.mark.anyio
async def test_run_sla_monitor_engineering_ok(
    client, db_session, create_unit, create_user, auth_header_for_user
) -> None:
    unit = create_unit(code="U-MON-02", name="Unidade Monitor Eng")
    eng = create_user(email="eng-mon@local.test", role=UserRole.ENGINEERING)

    response = await client.post("/alerts/run-sla-monitor", headers=auth_header_for_user(eng))
    assert response.status_code == 200


@pytest.mark.anyio
async def test_run_sla_monitor_manager_forbidden(
    client, create_unit, create_user, auth_header_for_user
) -> None:
    unit = create_unit(code="U-MON-03", name="Unidade Monitor Mgr")
    manager = create_user(email="mgr-mon@local.test", role=UserRole.MANAGER, unit_id=unit.id)

    response = await client.post("/alerts/run-sla-monitor", headers=auth_header_for_user(manager))
    assert response.status_code == 403


@pytest.mark.anyio
async def test_run_sla_monitor_director_forbidden(
    client, create_user, auth_header_for_user
) -> None:
    director = create_user(email="dir-mon@local.test", role=UserRole.DIRECTOR)
    response = await client.post("/alerts/run-sla-monitor", headers=auth_header_for_user(director))
    assert response.status_code == 403


@pytest.mark.anyio
async def test_run_sla_monitor_returns_summary_structure(
    client, create_user, auth_header_for_user
) -> None:
    admin = create_user(email="admin-mon2@local.test", role=UserRole.ADMIN)
    response = await client.post("/alerts/run-sla-monitor", headers=auth_header_for_user(admin))
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data["checked_tickets"], int)
    assert isinstance(data["created_alerts"], int)
    assert isinstance(data["skipped_duplicates"], int)


# ---------------------------------------------------------------------------
# Pagination
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_alerts_pagination(
    client, db_session, create_unit, create_user, auth_header_for_user
) -> None:
    unit = create_unit(code="U-PAGE-01", name="Unidade Paginacao")
    admin = create_user(email="admin-page@local.test", role=UserRole.ADMIN)
    now = datetime.now(UTC)

    for i in range(5):
        ticket = _create_ticket(
            db_session,
            unit_id=unit.id,
            opened_by_user_id=admin.id,
            ticket_number=f"PAGE-{i:03d}",
            status=TicketStatus.OPEN,
            sla_due_at=now - timedelta(hours=1),
        )
        _create_alert(db_session, ticket_id=ticket.id, alert_type=AlertType.SLA_LATE)

    headers = auth_header_for_user(admin)
    resp = await client.get("/alerts?page=1&page_size=3", headers=headers)
    data = resp.json()
    assert data["total"] == 5
    assert len(data["items"]) == 3
    assert data["pages"] == 2


# ---------------------------------------------------------------------------
# Regression: existing routes still work
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_tickets_endpoint_still_works(client, create_user, auth_header_for_user) -> None:
    admin = create_user(email="admin-reg@local.test", role=UserRole.ADMIN)
    response = await client.get("/tickets", headers=auth_header_for_user(admin))
    assert response.status_code == 200


@pytest.mark.anyio
async def test_suppliers_endpoint_still_works(client, create_user, auth_header_for_user) -> None:
    admin = create_user(email="admin-reg2@local.test", role=UserRole.ADMIN)
    response = await client.get("/suppliers", headers=auth_header_for_user(admin))
    assert response.status_code == 200
