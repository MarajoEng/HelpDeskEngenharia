"""FASE 10 — testes do encerramento com evidencia."""
from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

import httpx
import pytest

from app.core.config import get_settings
from app.models.enums import TicketStatus, UserRole
from app.models.ticket import Ticket
from app.models.ticket_attachment import TicketAttachment


def _create_ticket(
    db_session,
    *,
    unit_id: int,
    opened_by_user_id: int,
    status: TicketStatus = TicketStatus.IN_PROGRESS,
    requires_approval: bool = False,
    **overrides: object,
) -> Ticket:
    now = datetime.now(UTC)
    ticket = Ticket(
        ticket_number=f"ENG-{now.strftime('%Y%m%d')}-{int(now.timestamp() * 1000)}",
        unit_id=unit_id,
        opened_by_user_id=opened_by_user_id,
        assigned_to_user_id=None,
        category="fuel_pump",
        problem_type="Falha hidraulica",
        title="Bomba parada",
        description="Descricao do problema",
        priority="high",
        severity="critical",
        status=status,
        requires_approval=requires_approval,
        opened_at=now - timedelta(hours=10),
        triaged_at=now - timedelta(hours=9),
        started_at=now - timedelta(hours=8) if status in {TicketStatus.IN_PROGRESS, TicketStatus.RESOLVED, TicketStatus.CLOSED} else None,
        resolved_at=now - timedelta(hours=3) if status in {TicketStatus.RESOLVED, TicketStatus.CLOSED} else None,
        closed_at=now - timedelta(hours=1) if status == TicketStatus.CLOSED else None,
        final_cost="250.00" if status in {TicketStatus.RESOLVED, TicketStatus.CLOSED} else None,
    )
    for field, value in overrides.items():
        setattr(ticket, field, value)
    db_session.add(ticket)
    db_session.commit()
    db_session.refresh(ticket)
    return ticket


def _create_attachment_record(
    db_session,
    *,
    ticket_id: int,
    uploaded_by_user_id: int,
    attachment_type: str = "closing_evidence",
    file_type: str = "application/pdf",
    stored_file_url: str | None = None,
) -> TicketAttachment:
    attachment = TicketAttachment(
        ticket_id=ticket_id,
        uploaded_by_user_id=uploaded_by_user_id,
        file_url=stored_file_url or f"tickets/{ticket_id}/manual.pdf",
        file_type=file_type,
        attachment_type=attachment_type,
    )
    db_session.add(attachment)
    db_session.commit()
    db_session.refresh(attachment)
    return attachment


def _write_attachment_file(relative_path: str, content: bytes = b"pdf-content") -> None:
    root = Path(get_settings().upload_dir)
    target = root / relative_path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(content)


def _multipart_file(filename: str = "evidencia.pdf", content: bytes = b"fake-pdf", content_type: str = "application/pdf"):
    return {"file": (filename, content, content_type)}


@pytest.mark.anyio
async def test_admin_uploads_closing_evidence(
    client: httpx.AsyncClient,
    create_unit,
    create_user,
    db_session,
    auth_header_for_user,
) -> None:
    unit = create_unit()
    admin = create_user(role=UserRole.ADMIN)
    ticket = _create_ticket(db_session, unit_id=unit.id, opened_by_user_id=admin.id)

    response = await client.post(
        f"/tickets/{ticket.id}/attachments",
        headers=auth_header_for_user(admin),
        data={"attachment_type": "closing_evidence"},
        files=_multipart_file(),
    )

    assert response.status_code == 201
    data = response.json()
    assert data["ticket_id"] == ticket.id
    assert data["attachment_type"] == "closing_evidence"
    assert data["uploaded_by_user_id"] == admin.id
    assert data["file_url"].startswith("/attachments/")
    assert str(get_settings().upload_dir) not in data["file_url"]


@pytest.mark.anyio
async def test_engineering_uploads_closing_evidence(
    client: httpx.AsyncClient,
    create_unit,
    create_user,
    db_session,
    auth_header_for_user,
) -> None:
    unit = create_unit()
    admin = create_user(role=UserRole.ADMIN)
    engineer = create_user(role=UserRole.ENGINEERING, email="eng-upload@local.test")
    ticket = _create_ticket(db_session, unit_id=unit.id, opened_by_user_id=admin.id)

    response = await client.post(
        f"/tickets/{ticket.id}/attachments",
        headers=auth_header_for_user(engineer),
        data={"attachment_type": "closing_evidence"},
        files=_multipart_file("foto.png", b"png-data", "image/png"),
    )

    assert response.status_code == 201
    assert response.json()["file_type"] == "image/png"


@pytest.mark.anyio
async def test_manager_uploads_attachment_in_own_unit(
    client: httpx.AsyncClient,
    create_unit,
    create_user,
    db_session,
    auth_header_for_user,
) -> None:
    unit = create_unit()
    manager = create_user(role=UserRole.MANAGER, email="manager@local.test", unit_id=unit.id)
    opener = create_user(role=UserRole.ADMIN, email="admin-own@local.test")
    ticket = _create_ticket(db_session, unit_id=unit.id, opened_by_user_id=opener.id)

    response = await client.post(
        f"/tickets/{ticket.id}/attachments",
        headers=auth_header_for_user(manager),
        data={"attachment_type": "progress_evidence"},
        files=_multipart_file("foto.webp", b"webp-data", "image/webp"),
    )

    assert response.status_code == 201
    assert response.json()["attachment_type"] == "progress_evidence"


@pytest.mark.anyio
async def test_manager_cannot_upload_attachment_in_other_unit(
    client: httpx.AsyncClient,
    create_unit,
    create_user,
    db_session,
    auth_header_for_user,
) -> None:
    own_unit = create_unit(code="U-001")
    other_unit = create_unit(code="U-002", name="Outra unidade")
    manager = create_user(role=UserRole.MANAGER, email="manager-other@local.test", unit_id=own_unit.id)
    opener = create_user(role=UserRole.ADMIN, email="admin-other@local.test")
    ticket = _create_ticket(db_session, unit_id=other_unit.id, opened_by_user_id=opener.id)

    response = await client.post(
        f"/tickets/{ticket.id}/attachments",
        headers=auth_header_for_user(manager),
        data={"attachment_type": "closing_evidence"},
        files=_multipart_file(),
    )

    assert response.status_code == 403


@pytest.mark.anyio
async def test_supplier_and_director_cannot_upload_attachment(
    client: httpx.AsyncClient,
    create_unit,
    create_user,
    db_session,
    auth_header_for_user,
) -> None:
    unit = create_unit()
    admin = create_user(role=UserRole.ADMIN)
    supplier = create_user(role=UserRole.SUPPLIER, email="supplier-upload@local.test")
    director = create_user(role=UserRole.DIRECTOR, email="director-upload@local.test")
    ticket = _create_ticket(db_session, unit_id=unit.id, opened_by_user_id=admin.id)

    supplier_response = await client.post(
        f"/tickets/{ticket.id}/attachments",
        headers=auth_header_for_user(supplier),
        data={"attachment_type": "closing_evidence"},
        files=_multipart_file(),
    )
    director_response = await client.post(
        f"/tickets/{ticket.id}/attachments",
        headers=auth_header_for_user(director),
        data={"attachment_type": "closing_evidence"},
        files=_multipart_file(),
    )

    assert supplier_response.status_code == 403
    assert director_response.status_code == 403


@pytest.mark.anyio
async def test_upload_rejects_invalid_type_and_large_file(
    client: httpx.AsyncClient,
    create_unit,
    create_user,
    db_session,
    auth_header_for_user,
) -> None:
    unit = create_unit()
    admin = create_user(role=UserRole.ADMIN)
    ticket = _create_ticket(db_session, unit_id=unit.id, opened_by_user_id=admin.id)

    invalid_type_response = await client.post(
        f"/tickets/{ticket.id}/attachments",
        headers=auth_header_for_user(admin),
        data={"attachment_type": "closing_evidence"},
        files=_multipart_file("arquivo.txt", b"texto", "text/plain"),
    )
    large_file_response = await client.post(
        f"/tickets/{ticket.id}/attachments",
        headers=auth_header_for_user(admin),
        data={"attachment_type": "closing_evidence"},
        files=_multipart_file("grande.pdf", b"x" * (1024 * 1024 + 1), "application/pdf"),
    )

    assert invalid_type_response.status_code == 422
    assert large_file_response.status_code == 422


@pytest.mark.anyio
async def test_attachment_listing_and_download_respect_permission(
    client: httpx.AsyncClient,
    create_unit,
    create_user,
    db_session,
    auth_header_for_user,
) -> None:
    unit = create_unit()
    admin = create_user(role=UserRole.ADMIN)
    manager = create_user(role=UserRole.MANAGER, email="manager-list@local.test", unit_id=unit.id)
    director = create_user(role=UserRole.DIRECTOR, email="director-list@local.test")
    supplier = create_user(role=UserRole.SUPPLIER, email="supplier-list@local.test")
    ticket = _create_ticket(db_session, unit_id=unit.id, opened_by_user_id=admin.id)
    attachment = _create_attachment_record(db_session, ticket_id=ticket.id, uploaded_by_user_id=admin.id)
    _write_attachment_file(attachment.file_url, b"downloadable")

    manager_list = await client.get(f"/tickets/{ticket.id}/attachments", headers=auth_header_for_user(manager))
    director_download = await client.get(
        f"/attachments/{attachment.id}/download",
        headers=auth_header_for_user(director),
    )
    supplier_list = await client.get(f"/tickets/{ticket.id}/attachments", headers=auth_header_for_user(supplier))
    no_auth_download = await client.get(f"/attachments/{attachment.id}/download")

    assert manager_list.status_code == 200
    assert manager_list.json()["items"][0]["id"] == attachment.id
    assert director_download.status_code == 200
    assert director_download.content == b"downloadable"
    assert supplier_list.status_code == 403
    assert no_auth_download.status_code == 401


@pytest.mark.anyio
async def test_engineering_resolves_ticket_with_closing_evidence(
    client: httpx.AsyncClient,
    create_unit,
    create_user,
    db_session,
    auth_header_for_user,
) -> None:
    unit = create_unit()
    admin = create_user(role=UserRole.ADMIN)
    engineer = create_user(role=UserRole.ENGINEERING, email="eng-resolve@local.test")
    ticket = _create_ticket(db_session, unit_id=unit.id, opened_by_user_id=admin.id)
    _create_attachment_record(db_session, ticket_id=ticket.id, uploaded_by_user_id=engineer.id)

    response = await client.patch(
        f"/tickets/{ticket.id}/resolve",
        headers=auth_header_for_user(engineer),
        json={"solution_description": "Troca de conexao e validacao final.", "final_cost": "489.90"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "resolved"
    assert data["resolved_at"] is not None
    assert data["final_cost"] == "489.90"
    assert data["history"][-1]["new_status"] == "resolved"
    assert data["history"][-1]["comment"] == "Troca de conexao e validacao final."


@pytest.mark.anyio
async def test_admin_resolves_ticket_and_permissions_are_enforced(
    client: httpx.AsyncClient,
    create_unit,
    create_user,
    db_session,
    auth_header_for_user,
) -> None:
    unit = create_unit()
    admin = create_user(role=UserRole.ADMIN)
    manager = create_user(role=UserRole.MANAGER, email="manager-resolve@local.test", unit_id=unit.id)
    director = create_user(role=UserRole.DIRECTOR, email="director-resolve@local.test")
    supplier = create_user(role=UserRole.SUPPLIER, email="supplier-resolve@local.test")
    ticket = _create_ticket(db_session, unit_id=unit.id, opened_by_user_id=admin.id)
    _create_attachment_record(db_session, ticket_id=ticket.id, uploaded_by_user_id=admin.id)

    admin_response = await client.patch(
        f"/tickets/{ticket.id}/resolve",
        headers=auth_header_for_user(admin),
        json={"solution_description": "Servico concluido.", "final_cost": "300.00"},
    )
    manager_response = await client.patch(
        f"/tickets/{ticket.id}/resolve",
        headers=auth_header_for_user(manager),
        json={"solution_description": "Nao pode.", "final_cost": "10.00"},
    )
    director_response = await client.patch(
        f"/tickets/{ticket.id}/resolve",
        headers=auth_header_for_user(director),
        json={"solution_description": "Nao pode.", "final_cost": "10.00"},
    )
    supplier_response = await client.patch(
        f"/tickets/{ticket.id}/resolve",
        headers=auth_header_for_user(supplier),
        json={"solution_description": "Nao pode.", "final_cost": "10.00"},
    )

    assert admin_response.status_code == 200
    assert manager_response.status_code == 403
    assert director_response.status_code == 403
    assert supplier_response.status_code == 403


@pytest.mark.anyio
async def test_resolve_requires_closing_evidence_and_valid_payload(
    client: httpx.AsyncClient,
    create_unit,
    create_user,
    db_session,
    auth_header_for_user,
) -> None:
    unit = create_unit()
    admin = create_user(role=UserRole.ADMIN)
    ticket = _create_ticket(db_session, unit_id=unit.id, opened_by_user_id=admin.id)

    no_evidence = await client.patch(
        f"/tickets/{ticket.id}/resolve",
        headers=auth_header_for_user(admin),
        json={"solution_description": "Sem evidencia.", "final_cost": "10.00"},
    )
    missing_description = await client.patch(
        f"/tickets/{ticket.id}/resolve",
        headers=auth_header_for_user(admin),
        json={"solution_description": "   ", "final_cost": "10.00"},
    )
    negative_cost = await client.patch(
        f"/tickets/{ticket.id}/resolve",
        headers=auth_header_for_user(admin),
        json={"solution_description": "Descricao valida.", "final_cost": "-1.00"},
    )

    assert no_evidence.status_code == 422
    assert missing_description.status_code == 422
    assert negative_cost.status_code == 422


@pytest.mark.anyio
async def test_resolve_fails_outside_in_progress(
    client: httpx.AsyncClient,
    create_unit,
    create_user,
    db_session,
    auth_header_for_user,
) -> None:
    unit = create_unit()
    admin = create_user(role=UserRole.ADMIN)
    ticket = _create_ticket(db_session, unit_id=unit.id, opened_by_user_id=admin.id, status=TicketStatus.TRIAGE)
    _create_attachment_record(db_session, ticket_id=ticket.id, uploaded_by_user_id=admin.id)

    response = await client.patch(
        f"/tickets/{ticket.id}/resolve",
        headers=auth_header_for_user(admin),
        json={"solution_description": "Nao deveria resolver.", "final_cost": "50.00"},
    )

    assert response.status_code == 409


@pytest.mark.anyio
async def test_engineering_and_admin_can_close_ticket(
    client: httpx.AsyncClient,
    create_unit,
    create_user,
    db_session,
    auth_header_for_user,
) -> None:
    unit = create_unit()
    admin = create_user(role=UserRole.ADMIN)
    engineer = create_user(role=UserRole.ENGINEERING, email="eng-close@local.test")
    ticket = _create_ticket(
        db_session,
        unit_id=unit.id,
        opened_by_user_id=admin.id,
        status=TicketStatus.RESOLVED,
        resolved_at=datetime.now(UTC) - timedelta(hours=2),
        final_cost="550.00",
    )

    engineer_response = await client.patch(
        f"/tickets/{ticket.id}/close",
        headers=auth_header_for_user(engineer),
        json={"close_comment": "Validacao final concluida."},
    )

    second_ticket = _create_ticket(
        db_session,
        unit_id=unit.id,
        opened_by_user_id=admin.id,
        status=TicketStatus.RESOLVED,
        resolved_at=datetime.now(UTC) - timedelta(hours=1),
        final_cost="350.00",
    )
    admin_response = await client.patch(
        f"/tickets/{second_ticket.id}/close",
        headers=auth_header_for_user(admin),
        json={"close_comment": "Encerramento administrativo."},
    )

    assert engineer_response.status_code == 200
    assert engineer_response.json()["status"] == "closed"
    assert engineer_response.json()["closed_at"] is not None
    assert engineer_response.json()["history"][-1]["comment"] == "Validacao final concluida."
    assert admin_response.status_code == 200
    assert admin_response.json()["status"] == "closed"


@pytest.mark.anyio
async def test_close_requires_resolved_status_and_comment(
    client: httpx.AsyncClient,
    create_unit,
    create_user,
    db_session,
    auth_header_for_user,
) -> None:
    unit = create_unit()
    admin = create_user(role=UserRole.ADMIN)
    manager = create_user(role=UserRole.MANAGER, email="manager-close@local.test", unit_id=unit.id)
    supplier = create_user(role=UserRole.SUPPLIER, email="supplier-close@local.test")
    in_progress_ticket = _create_ticket(db_session, unit_id=unit.id, opened_by_user_id=admin.id)
    resolved_ticket = _create_ticket(
        db_session,
        unit_id=unit.id,
        opened_by_user_id=admin.id,
        status=TicketStatus.RESOLVED,
        resolved_at=datetime.now(UTC) - timedelta(hours=1),
        final_cost="100.00",
    )

    wrong_status = await client.patch(
        f"/tickets/{in_progress_ticket.id}/close",
        headers=auth_header_for_user(admin),
        json={"close_comment": "Nao deveria fechar."},
    )
    missing_comment = await client.patch(
        f"/tickets/{resolved_ticket.id}/close",
        headers=auth_header_for_user(admin),
        json={"close_comment": "   "},
    )
    manager_response = await client.patch(
        f"/tickets/{resolved_ticket.id}/close",
        headers=auth_header_for_user(manager),
        json={"close_comment": "Sem permissao."},
    )
    supplier_response = await client.patch(
        f"/tickets/{resolved_ticket.id}/close",
        headers=auth_header_for_user(supplier),
        json={"close_comment": "Sem permissao."},
    )

    assert wrong_status.status_code == 409
    assert missing_comment.status_code == 422
    assert manager_response.status_code == 403
    assert supplier_response.status_code == 403


@pytest.mark.anyio
async def test_ticket_detail_returns_attachments_and_final_indicators(
    client: httpx.AsyncClient,
    create_unit,
    create_user,
    db_session,
    auth_header_for_user,
) -> None:
    unit = create_unit()
    admin = create_user(role=UserRole.ADMIN)
    ticket = _create_ticket(
        db_session,
        unit_id=unit.id,
        opened_by_user_id=admin.id,
        status=TicketStatus.CLOSED,
        opened_at=datetime.now(UTC) - timedelta(hours=10),
        resolved_at=datetime.now(UTC) - timedelta(hours=4),
        closed_at=datetime.now(UTC) - timedelta(hours=1),
        final_cost="700.00",
    )
    attachment = _create_attachment_record(db_session, ticket_id=ticket.id, uploaded_by_user_id=admin.id)

    response = await client.get(f"/tickets/{ticket.id}", headers=auth_header_for_user(admin))

    assert response.status_code == 200
    data = response.json()
    assert data["attachments"][0]["id"] == attachment.id
    assert data["attachments"][0]["file_url"].startswith("/attachments/")
    assert str(get_settings().upload_dir) not in data["attachments"][0]["file_url"]
    assert data["indicators"]["has_closing_evidence"] is True
    assert data["indicators"]["final_cost"] == "700.00"
    assert data["indicators"]["total_hours"] == 9.0
    assert data["indicators"]["resolution_hours"] == 6.0
    assert data["indicators"]["closure_hours"] == 3.0
