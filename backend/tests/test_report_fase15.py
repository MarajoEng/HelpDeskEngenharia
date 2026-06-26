"""FASE 15 — Relatorios e exportacao CSV."""
from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import httpx
import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.audit_log import AuditLog
from app.models.enums import TicketStatus, UserRole
from app.models.supplier import Supplier
from app.models.ticket import Ticket
from app.services.ticket_configuration_seed import seed_ticket_configurations


def _create_supplier(
    db_session: Session,
    *,
    name: str,
    specialty: str,
    is_active: bool = True,
) -> Supplier:
    supplier = Supplier(
        name=name,
        document=f"{name[:4].upper():0<4}00010001",
        phone="11999999999",
        email=f"{name.lower().replace(' ', '_')}@test.com",
        specialty=specialty,
        is_active=is_active,
    )
    db_session.add(supplier)
    db_session.commit()
    db_session.refresh(supplier)
    return supplier


def _create_ticket(
    db_session: Session,
    *,
    unit_id: int,
    opened_by_user_id: int,
    ticket_number: str,
    status: TicketStatus,
    category: str = "fuel_pump",
    category_id: int | None = None,
    subcategory_id: int | None = None,
    type_id: int | None = None,
    priority: str = "medium",
    priority_id: int | None = None,
    severity: str = "medium",
    supplier_id: int | None = None,
    opened_at: datetime | None = None,
    started_at: datetime | None = None,
    resolved_at: datetime | None = None,
    closed_at: datetime | None = None,
    sla_due_at: datetime | None = None,
    expected_resolution_at: datetime | None = None,
    estimated_daily_loss: str | Decimal | None = None,
    estimated_cost: str | Decimal | None = None,
    approved_cost: str | Decimal | None = None,
    final_cost: str | Decimal | None = None,
    fuel_nozzles_stopped: int | None = None,
    requires_approval: bool = False,
) -> Ticket:
    ticket = Ticket(
        ticket_number=ticket_number,
        unit_id=unit_id,
        opened_by_user_id=opened_by_user_id,
        assigned_to_user_id=None,
        category_id=category_id,
        subcategory_id=subcategory_id,
        type_id=type_id,
        category=category,
        problem_type="Falha operacional",
        title=f"Chamado {ticket_number}",
        description="Descricao do chamado",
        priority=priority,
        priority_id=priority_id,
        severity=severity,
        status=status,
        supplier_id=supplier_id,
        opened_at=opened_at or datetime.now(UTC),
        started_at=started_at,
        resolved_at=resolved_at,
        closed_at=closed_at,
        sla_due_at=sla_due_at,
        expected_resolution_at=expected_resolution_at,
        estimated_daily_loss=estimated_daily_loss,
        estimated_cost=estimated_cost,
        approved_cost=approved_cost,
        final_cost=final_cost,
        fuel_nozzles_stopped=fuel_nozzles_stopped,
        requires_approval=requires_approval,
    )
    db_session.add(ticket)
    db_session.commit()
    db_session.refresh(ticket)
    return ticket


def _seed_report_dataset(db_session: Session, create_unit, create_user) -> dict[str, object]:
    base_now = datetime.now(UTC)
    unit_1 = create_unit(code="R-001", name="Unidade Norte", region="Norte")
    unit_2 = create_unit(code="R-002", name="Unidade Sul", region="Sul")

    admin = create_user(role=UserRole.ADMIN, email="report_admin@test.com")
    engineering = create_user(role=UserRole.ENGINEERING, email="report_engineering@test.com")
    director = create_user(role=UserRole.DIRECTOR, email="report_director@test.com")
    manager = create_user(role=UserRole.MANAGER, email="report_manager@test.com", unit_id=unit_1.id)
    supplier_user = create_user(role=UserRole.SUPPLIER, email="report_supplier@test.com")

    supplier_a = _create_supplier(db_session, name="Fornecedor Alfa", specialty="Eletrica")
    supplier_b = _create_supplier(db_session, name="Fornecedor Beta", specialty="Estrutural")

    _create_ticket(
        db_session,
        unit_id=unit_1.id,
        opened_by_user_id=admin.id,
        ticket_number="REP-001",
        status=TicketStatus.OPEN,
        category="electrical",
        priority="high",
        severity="critical",
        opened_at=base_now - timedelta(days=1),
        sla_due_at=base_now + timedelta(hours=6),
        estimated_daily_loss="1000.00",
        estimated_cost="200.00",
        fuel_nozzles_stopped=2,
        requires_approval=True,
    )
    _create_ticket(
        db_session,
        unit_id=unit_1.id,
        opened_by_user_id=admin.id,
        ticket_number="REP-002",
        status=TicketStatus.IN_PROGRESS,
        category="structure",
        priority="critical",
        severity="critical",
        supplier_id=supplier_a.id,
        opened_at=base_now - timedelta(days=2),
        started_at=base_now - timedelta(days=2) + timedelta(hours=2),
        sla_due_at=base_now - timedelta(hours=3),
        expected_resolution_at=base_now - timedelta(hours=2),
        estimated_cost="300.00",
        approved_cost="280.00",
        fuel_nozzles_stopped=1,
    )
    _create_ticket(
        db_session,
        unit_id=unit_1.id,
        opened_by_user_id=admin.id,
        ticket_number="REP-003",
        status=TicketStatus.CLOSED,
        category="electrical",
        priority="medium",
        severity="medium",
        supplier_id=supplier_a.id,
        opened_at=base_now - timedelta(days=4),
        started_at=base_now - timedelta(days=4) + timedelta(hours=5),
        resolved_at=base_now - timedelta(days=3),
        closed_at=base_now - timedelta(days=2, hours=20),
        sla_due_at=base_now - timedelta(days=2, hours=12),
        expected_resolution_at=base_now - timedelta(days=3, hours=2),
        estimated_cost="180.00",
        approved_cost="170.00",
        final_cost="160.00",
    )
    _create_ticket(
        db_session,
        unit_id=unit_2.id,
        opened_by_user_id=admin.id,
        ticket_number="REP-004",
        status=TicketStatus.RESOLVED,
        category="roof",
        priority="low",
        severity="high",
        supplier_id=supplier_b.id,
        opened_at=base_now - timedelta(days=3),
        started_at=base_now - timedelta(days=3) + timedelta(hours=3),
        resolved_at=base_now - timedelta(days=1),
        sla_due_at=base_now + timedelta(hours=1),
        expected_resolution_at=base_now - timedelta(days=1, hours=4),
        estimated_cost="500.00",
        approved_cost="450.00",
        final_cost="430.00",
    )
    _create_ticket(
        db_session,
        unit_id=unit_2.id,
        opened_by_user_id=admin.id,
        ticket_number="REP-005",
        status=TicketStatus.CLOSED,
        category="roof",
        priority="medium",
        severity="low",
        supplier_id=supplier_b.id,
        opened_at=base_now - timedelta(days=10),
        started_at=base_now - timedelta(days=9, hours=20),
        resolved_at=base_now - timedelta(days=8),
        closed_at=base_now - timedelta(days=7, hours=20),
        sla_due_at=base_now - timedelta(days=8, hours=2),
        expected_resolution_at=base_now - timedelta(days=8, hours=6),
        estimated_cost="220.00",
        approved_cost="210.00",
        final_cost="205.00",
    )
    _create_ticket(
        db_session,
        unit_id=unit_2.id,
        opened_by_user_id=admin.id,
        ticket_number="REP-006",
        status=TicketStatus.OPEN,
        category="other",
        priority="low",
        severity="low",
        opened_at=base_now - timedelta(days=40),
        sla_due_at=base_now - timedelta(days=39),
        estimated_cost="80.00",
    )

    return {
        "unit_1": unit_1,
        "unit_2": unit_2,
        "admin": admin,
        "engineering": engineering,
        "director": director,
        "manager": manager,
        "supplier_user": supplier_user,
        "supplier_a": supplier_a,
        "supplier_b": supplier_b,
    }


def _audit_logs_for(db_session: Session, action: str) -> list[AuditLog]:
    return list(db_session.scalars(select(AuditLog).where(AuditLog.action == action)).all())


@pytest.mark.anyio
async def test_report_access_permissions(
    client: httpx.AsyncClient,
    db_session: Session,
    create_unit,
    create_user,
    auth_header_for_user,
) -> None:
    data = _seed_report_dataset(db_session, create_unit, create_user)

    assert (await client.get("/reports/tickets", headers=auth_header_for_user(data["admin"]))).status_code == 200
    assert (await client.get("/reports/tickets", headers=auth_header_for_user(data["director"]))).status_code == 200
    assert (await client.get("/reports/tickets", headers=auth_header_for_user(data["engineering"]))).status_code == 200
    assert (await client.get("/reports/tickets", headers=auth_header_for_user(data["manager"]))).status_code == 200
    assert (await client.get("/reports/tickets", headers=auth_header_for_user(data["supplier_user"]))).status_code == 403
    assert (await client.get("/reports/tickets")).status_code == 401


@pytest.mark.anyio
async def test_manager_scope_and_ticket_filters(
    client: httpx.AsyncClient,
    db_session: Session,
    create_unit,
    create_user,
    auth_header_for_user,
) -> None:
    data = _seed_report_dataset(db_session, create_unit, create_user)
    manager_headers = auth_header_for_user(data["manager"])
    admin_headers = auth_header_for_user(data["admin"])

    manager_response = await client.get("/reports/tickets", headers=manager_headers)
    blocked_response = await client.get(
        f"/reports/tickets?unit_id={data['unit_2'].id}",
        headers=manager_headers,
    )
    status_response = await client.get("/reports/tickets?status=in_progress", headers=admin_headers)
    category_response = await client.get("/reports/tickets?category=roof", headers=admin_headers)
    unit_response = await client.get(
        f"/reports/tickets?unit_id={data['unit_1'].id}",
        headers=admin_headers,
    )
    period_from = (datetime.now(UTC).date() - timedelta(days=2)).isoformat()
    period_to = datetime.now(UTC).date().isoformat()
    period_response = await client.get(
        f"/reports/tickets?date_from={period_from}&date_to={period_to}",
        headers=admin_headers,
    )

    assert manager_response.status_code == 200
    manager_items = manager_response.json()["items"]
    assert len(manager_items) == 3
    assert all(item["unit_id"] == data["unit_1"].id for item in manager_items)
    assert blocked_response.status_code == 403
    assert status_response.status_code == 200
    assert status_response.json()["total"] == 1
    assert status_response.json()["items"][0]["ticket_number"] == "REP-002"
    assert category_response.status_code == 200
    assert category_response.json()["total"] == 2
    assert unit_response.status_code == 200
    assert unit_response.json()["total"] == 3
    assert period_response.status_code == 200
    assert period_response.json()["total"] == 2


@pytest.mark.anyio
async def test_ticket_report_returns_configured_names_and_filters_by_ids(
    client: httpx.AsyncClient,
    db_session: Session,
    create_unit,
    create_user,
    auth_header_for_user,
) -> None:
    seeded = seed_ticket_configurations(db_session)
    unit = create_unit(code="RC-001", name="Unidade Relatorio Config")
    admin = create_user(role=UserRole.ADMIN, email="report-config-admin@test.com")
    category = next(item for item in seeded["categories"] if item.legacy_value == "fuel_pump")
    priority = next(item for item in seeded["priorities"] if item.legacy_value == "high")

    _create_ticket(
        db_session,
        unit_id=unit.id,
        opened_by_user_id=admin.id,
        ticket_number="REP-CFG-001",
        status=TicketStatus.OPEN,
        category=category.legacy_value,
        category_id=category.id,
        priority=priority.legacy_value,
        priority_id=priority.id,
    )

    response = await client.get(
        f"/reports/tickets?category_id={category.id}&priority_id={priority.id}",
        headers=auth_header_for_user(admin),
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 1
    item = payload["items"][0]
    assert item["category_id"] == category.id
    assert item["category_name"] == category.name
    assert item["priority_id"] == priority.id
    assert item["priority_name"] == priority.name
    assert item["priority_color"] == priority.color
    assert item["priority_weight"] == priority.weight


@pytest.mark.anyio
async def test_ticket_report_keeps_legacy_ticket_without_configured_ids(
    client: httpx.AsyncClient,
    db_session: Session,
    create_unit,
    create_user,
    auth_header_for_user,
) -> None:
    unit = create_unit(code="RL-001", name="Unidade Relatorio Legado")
    admin = create_user(role=UserRole.ADMIN, email="report-legacy-admin@test.com")
    _create_ticket(
        db_session,
        unit_id=unit.id,
        opened_by_user_id=admin.id,
        ticket_number="REP-LEG-001",
        status=TicketStatus.OPEN,
        category="electrical",
        priority="medium",
    )

    response = await client.get("/reports/tickets?category=electrical", headers=auth_header_for_user(admin))

    assert response.status_code == 200
    item = response.json()["items"][0]
    assert item["category_id"] is None
    assert item["priority_id"] is None
    assert item["category_name"] == "Electrical"
    assert item["priority_name"] == "Media"


@pytest.mark.anyio
async def test_report_pagination_and_page_size_limit(
    client: httpx.AsyncClient,
    db_session: Session,
    create_unit,
    create_user,
    auth_header_for_user,
) -> None:
    data = _seed_report_dataset(db_session, create_unit, create_user)
    headers = auth_header_for_user(data["admin"])

    response = await client.get("/reports/tickets?page=1&page_size=2", headers=headers)
    assert response.status_code == 200
    payload = response.json()
    assert payload["page"] == 1
    assert payload["page_size"] == 2
    assert payload["pages"] == 3
    assert len(payload["items"]) == 2

    too_large = await client.get("/reports/tickets?page=1&page_size=101", headers=headers)
    assert too_large.status_code == 422


@pytest.mark.anyio
async def test_cost_report_aggregates_correctly(
    client: httpx.AsyncClient,
    db_session: Session,
    create_unit,
    create_user,
    auth_header_for_user,
) -> None:
    data = _seed_report_dataset(db_session, create_unit, create_user)
    response = await client.get(
        f"/reports/costs?unit_id={data['unit_2'].id}",
        headers=auth_header_for_user(data["admin"]),
    )

    assert response.status_code == 200
    items = response.json()["items"]
    roof_row = next(item for item in items if item["category"] == "roof")
    assert roof_row["total_tickets"] == 2
    assert roof_row["estimated_cost_total"] == "720.00"
    assert roof_row["approved_cost_total"] == "660.00"
    assert roof_row["final_cost_total"] == "635.00"


@pytest.mark.anyio
async def test_sla_and_unit_reports_aggregate_without_division_errors(
    client: httpx.AsyncClient,
    db_session: Session,
    create_unit,
    create_user,
    auth_header_for_user,
) -> None:
    data = _seed_report_dataset(db_session, create_unit, create_user)
    headers = auth_header_for_user(data["admin"])

    sla_response = await client.get("/reports/sla", headers=headers)
    unit_response = await client.get("/reports/units", headers=headers)
    empty_sla_response = await client.get(
        "/reports/sla?date_from=2100-01-01&date_to=2100-01-02",
        headers=headers,
    )

    assert sla_response.status_code == 200
    sla_items = sla_response.json()["items"]
    unit_1_sla = next(item for item in sla_items if item["unit_id"] == data["unit_1"].id)
    assert unit_1_sla["total_with_sla"] == 3
    assert unit_1_sla["on_track"] == 1
    assert unit_1_sla["late"] == 1
    assert unit_1_sla["closed_on_time"] == 1
    assert unit_1_sla["closed_late"] == 0
    assert unit_1_sla["compliance_rate"] == pytest.approx(66.67, rel=1e-2)

    assert empty_sla_response.status_code == 200
    assert empty_sla_response.json()["items"] == []
    assert empty_sla_response.json()["total"] == 0

    assert unit_response.status_code == 200
    unit_items = unit_response.json()["items"]
    unit_2_row = next(item for item in unit_items if item["unit_id"] == data["unit_2"].id)
    assert unit_2_row["total_tickets"] == 3
    assert unit_2_row["closed_tickets"] == 1
    assert unit_2_row["final_cost_total"] == "635.00"


@pytest.mark.anyio
async def test_supplier_report_aggregates_correctly(
    client: httpx.AsyncClient,
    db_session: Session,
    create_unit,
    create_user,
    auth_header_for_user,
) -> None:
    data = _seed_report_dataset(db_session, create_unit, create_user)
    response = await client.get("/reports/suppliers", headers=auth_header_for_user(data["admin"]))

    assert response.status_code == 200
    items = response.json()["items"]
    supplier_a_row = next(item for item in items if item["supplier_name"] == "Fornecedor Alfa")
    assert supplier_a_row["total_tickets"] == 2
    assert supplier_a_row["in_progress_tickets"] == 1
    assert supplier_a_row["closed_tickets"] == 1
    assert supplier_a_row["late_execution_tickets"] >= 1


@pytest.mark.anyio
@pytest.mark.parametrize(
    ("path", "expected_prefix"),
    [
        ("/reports/tickets/export.csv", "ticket_number,unit_code"),
        ("/reports/costs/export.csv", "unit_code,unit_name"),
        ("/reports/sla/export.csv", "unit_code,unit_name"),
        ("/reports/units/export.csv", "unit_code,unit_name"),
        ("/reports/suppliers/export.csv", "supplier_name,total_tickets"),
    ],
)
async def test_csv_exports_return_headers_and_audit_logs(
    client: httpx.AsyncClient,
    db_session: Session,
    create_unit,
    create_user,
    auth_header_for_user,
    path: str,
    expected_prefix: str,
) -> None:
    data = _seed_report_dataset(db_session, create_unit, create_user)
    response = await client.get(path, headers=auth_header_for_user(data["admin"]))

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    assert response.text.splitlines()[0].startswith(expected_prefix)

    export_logs = _audit_logs_for(db_session, "report_exported")
    assert len(export_logs) >= 1


@pytest.mark.anyio
async def test_csv_export_respects_manager_scope_and_supplier_block(
    client: httpx.AsyncClient,
    db_session: Session,
    create_unit,
    create_user,
    auth_header_for_user,
) -> None:
    data = _seed_report_dataset(db_session, create_unit, create_user)
    manager_headers = auth_header_for_user(data["manager"])
    supplier_headers = auth_header_for_user(data["supplier_user"])

    manager_response = await client.get("/reports/tickets/export.csv", headers=manager_headers)
    supplier_response = await client.get("/reports/tickets/export.csv", headers=supplier_headers)
    blocked_manager_response = await client.get(
        f"/reports/tickets/export.csv?unit_id={data['unit_2'].id}",
        headers=manager_headers,
    )

    assert manager_response.status_code == 200
    assert "REP-004" not in manager_response.text
    assert supplier_response.status_code == 403
    assert blocked_manager_response.status_code == 403


@pytest.mark.anyio
async def test_export_limit_returns_clear_message(
    client: httpx.AsyncClient,
    db_session: Session,
    create_unit,
    create_user,
    auth_header_for_user,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("REPORT_EXPORT_MAX_ROWS", "1")
    get_settings.cache_clear()
    data = _seed_report_dataset(db_session, create_unit, create_user)

    try:
        response = await client.get("/reports/tickets/export.csv", headers=auth_header_for_user(data["admin"]))
        assert response.status_code == 422
        assert "limite" in response.json()["detail"].lower()
    finally:
        get_settings.cache_clear()


@pytest.mark.anyio
async def test_report_view_creates_audit_log(
    client: httpx.AsyncClient,
    db_session: Session,
    create_unit,
    create_user,
    auth_header_for_user,
) -> None:
    data = _seed_report_dataset(db_session, create_unit, create_user)
    response = await client.get("/reports/units", headers=auth_header_for_user(data["admin"]))

    assert response.status_code == 200
    logs = _audit_logs_for(db_session, "report_viewed")
    assert len(logs) >= 1
    assert logs[-1].metadata_json["report_type"] == "units"
