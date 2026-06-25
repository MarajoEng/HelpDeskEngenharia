"""FASE 13 — Auditoria e segurança tests."""
from __future__ import annotations

import pytest
from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog
from app.models.enums import UserRole
from app.repositories.audit_repository import sanitize_metadata
from app.core.rate_limit import login_rate_limiter


# ── helpers ──────────────────────────────────────────────────────────────────

def _admin_headers(auth_header_for_user, create_user):
    admin = create_user(name="Audit Admin", email="audit_admin@test.com", role=UserRole.ADMIN)
    return auth_header_for_user(admin), admin


def _get_audit_logs(db_session: Session, action: str) -> list[AuditLog]:
    from sqlalchemy import select
    return list(db_session.scalars(select(AuditLog).where(AuditLog.action == action)).all())


# ── migration / config ────────────────────────────────────────────────────────

def test_audit_log_model_importable():
    from app.models.audit_log import AuditLog  # noqa: F401


def test_settings_has_cors_origins():
    from app.core.config import get_settings
    settings = get_settings()
    assert isinstance(settings.cors_origins, list)
    assert len(settings.cors_origins) > 0


def test_settings_has_rate_limit_fields():
    from app.core.config import get_settings
    settings = get_settings()
    assert settings.login_rate_limit_attempts >= 1
    assert settings.login_rate_limit_window_seconds >= 1


# ── sanitize_metadata ─────────────────────────────────────────────────────────

def test_sanitize_metadata_removes_password():
    raw = {"email": "a@b.com", "password": "secret", "name": "Joao"}
    result = sanitize_metadata(raw)
    assert "password" not in result
    assert result["email"] == "a@b.com"
    assert result["name"] == "Joao"


def test_sanitize_metadata_removes_token():
    raw = {"access_token": "tok123", "token": "tok", "user_id": 1}
    result = sanitize_metadata(raw)
    assert "access_token" not in result
    assert "token" not in result
    assert result["user_id"] == 1


def test_sanitize_metadata_removes_authorization():
    raw = {"authorization": "Bearer xyz", "entity": "user"}
    result = sanitize_metadata(raw)
    assert "authorization" not in result


def test_sanitize_metadata_removes_secret():
    raw = {"secret": "shh", "data": "ok"}
    result = sanitize_metadata(raw)
    assert "secret" not in result
    assert result["data"] == "ok"


def test_sanitize_metadata_preserves_safe_keys():
    raw = {"category": "electrical", "priority": "high", "role": "admin"}
    result = sanitize_metadata(raw)
    assert result == raw


def test_sanitize_metadata_empty_dict():
    assert sanitize_metadata({}) == {}


# ── security headers ──────────────────────────────────────────────────────────

@pytest.mark.anyio
async def test_security_headers_on_health(client):
    response = await client.get("/health/live")
    assert response.headers.get("x-content-type-options") == "nosniff"
    assert response.headers.get("x-frame-options") == "DENY"
    assert response.headers.get("referrer-policy") == "no-referrer"


@pytest.mark.anyio
async def test_security_headers_on_auth(client, create_user):
    create_user(name="HUser", email="huser@test.com", role=UserRole.ADMIN)
    response = await client.post("/auth/login", json={"email": "huser@test.com", "password": "admin123"})
    assert response.headers.get("x-content-type-options") == "nosniff"


# ── rate limiting ─────────────────────────────────────────────────────────────

@pytest.mark.anyio
async def test_login_rate_limit_blocks_after_limit(client, create_user, monkeypatch):
    from app.core.config import get_settings
    monkeypatch.setenv("LOGIN_RATE_LIMIT_ATTEMPTS", "3")
    get_settings.cache_clear()
    login_rate_limiter.clear_all()

    try:
        create_user(name="RL User", email="ratelimit_unique@test.com", role=UserRole.ADMIN, password="correct123")
        for _ in range(3):
            await client.post("/auth/login", json={"email": "ratelimit_unique@test.com", "password": "wrongpass"})

        response = await client.post("/auth/login", json={"email": "ratelimit_unique@test.com", "password": "wrongpass"})
        assert response.status_code == 429
        assert "tentativas" in response.json()["detail"].lower() or "muitas" in response.json()["detail"].lower()
    finally:
        login_rate_limiter.clear_all()
        get_settings.cache_clear()


@pytest.mark.anyio
async def test_login_rate_limit_not_triggered_on_success(client, create_user, monkeypatch):
    from app.core.config import get_settings
    monkeypatch.setenv("LOGIN_RATE_LIMIT_ATTEMPTS", "5")
    get_settings.cache_clear()
    login_rate_limiter.clear_all()

    try:
        create_user(name="OK User", email="ok_rate@test.com", role=UserRole.ADMIN, password="correct123")
        response = await client.post("/auth/login", json={"email": "ok_rate@test.com", "password": "correct123"})
        assert response.status_code == 200
    finally:
        login_rate_limiter.clear_all()
        get_settings.cache_clear()


def test_rate_limiter_clear_all():
    login_rate_limiter.check_and_record("testip:x@x.com")
    login_rate_limiter.clear_all()
    # After clear, should allow again
    assert login_rate_limiter.check_and_record("testip:x@x.com") is True


# ── audit log CRUD ────────────────────────────────────────────────────────────

@pytest.mark.anyio
async def test_audit_log_list_admin_only(client, create_user, auth_header_for_user):
    admin = create_user(name="AuditAdmin", email="aud_admin@test.com", role=UserRole.ADMIN)
    headers = auth_header_for_user(admin)
    response = await client.get("/audit-logs", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data


@pytest.mark.anyio
async def test_audit_log_list_forbidden_for_non_admin(client, create_user, auth_header_for_user):
    for role in [UserRole.ENGINEERING, UserRole.MANAGER, UserRole.DIRECTOR, UserRole.SUPPLIER]:
        user = create_user(name=f"User {role}", email=f"aud_{role.value}@test.com", role=role)
        headers = auth_header_for_user(user)
        response = await client.get("/audit-logs", headers=headers)
        assert response.status_code == 403, f"Expected 403 for {role}, got {response.status_code}"


@pytest.mark.anyio
async def test_audit_log_list_unauthenticated(client):
    response = await client.get("/audit-logs")
    assert response.status_code == 401


# ── audit log created for login ───────────────────────────────────────────────

@pytest.mark.anyio
async def test_audit_login_success_creates_log(client, create_user, auth_header_for_user, db_session):
    create_user(name="Login Audit", email="login_audit@test.com", role=UserRole.ADMIN, password="pass12345")
    response = await client.post("/auth/login", json={"email": "login_audit@test.com", "password": "pass12345"})
    assert response.status_code == 200

    logs = _get_audit_logs(db_session, "login_success")
    assert len(logs) >= 1
    assert logs[0].entity_type == "user"
    assert logs[0].actor_user_name == "Login Audit"


@pytest.mark.anyio
async def test_audit_login_failed_creates_log(client, create_user, db_session):
    create_user(name="Fail Audit", email="fail_audit@test.com", role=UserRole.ADMIN, password="correct")
    await client.post("/auth/login", json={"email": "fail_audit@test.com", "password": "wrong"})

    logs = _get_audit_logs(db_session, "login_failed")
    assert len(logs) >= 1
    assert logs[0].actor_user_id is None


# ── audit log created for user CRUD ──────────────────────────────────────────

@pytest.mark.anyio
async def test_audit_user_created(client, create_user, auth_header_for_user, db_session):
    admin = create_user(name="Admin2", email="admin2@test.com", role=UserRole.ADMIN)
    headers = auth_header_for_user(admin)
    await client.post("/users", headers=headers, json={
        "name": "Novo Usuario",
        "email": "novo_user_audit@test.com",
        "password": "pass12345",
        "role": "engineering",
    })

    logs = _get_audit_logs(db_session, "user_created")
    assert len(logs) >= 1
    assert logs[0].entity_type == "user"
    assert logs[0].actor_user_name == "Admin2"


@pytest.mark.anyio
async def test_audit_user_updated(client, create_user, auth_header_for_user, db_session):
    admin = create_user(name="Admin3", email="admin3@test.com", role=UserRole.ADMIN)
    target = create_user(name="Target", email="target_audit@test.com", role=UserRole.ENGINEERING)
    headers = auth_header_for_user(admin)
    await client.patch(f"/users/{target.id}", headers=headers, json={"name": "Target Updated"})

    logs = _get_audit_logs(db_session, "user_updated")
    assert len(logs) >= 1
    assert logs[0].entity_id == target.id


# ── audit log created for unit CRUD ──────────────────────────────────────────

@pytest.mark.anyio
async def test_audit_unit_created(client, create_user, auth_header_for_user, db_session):
    admin = create_user(name="Admin4", email="admin4@test.com", role=UserRole.ADMIN)
    headers = auth_header_for_user(admin)
    response = await client.post("/units", headers=headers, json={
        "code": "AUD-001",
        "name": "Unidade Auditoria",
        "city": "Campinas",
        "state": "SP",
        "region": "Sudeste",
    })
    assert response.status_code == 201

    logs = _get_audit_logs(db_session, "unit_created")
    assert len(logs) >= 1
    assert logs[0].entity_type == "unit"
    assert "AUD-001" in str(logs[0].metadata_json)


@pytest.mark.anyio
async def test_audit_unit_updated(client, create_user, create_unit, auth_header_for_user, db_session):
    admin = create_user(name="Admin5", email="admin5@test.com", role=UserRole.ADMIN)
    unit = create_unit(code="AUD-UPD", name="Unidade Update")
    headers = auth_header_for_user(admin)
    await client.patch(f"/units/{unit.id}", headers=headers, json={"name": "Unidade Atualizada"})

    logs = _get_audit_logs(db_session, "unit_updated")
    assert len(logs) >= 1
    assert logs[0].entity_id == unit.id


# ── audit log created for tickets ────────────────────────────────────────────

@pytest.mark.anyio
async def test_audit_ticket_created(client, create_user, create_unit, auth_header_for_user, db_session):
    admin = create_user(name="Admin6", email="admin6@test.com", role=UserRole.ADMIN)
    unit = create_unit(code="TKT-AUD", name="Unidade Ticket")
    admin2 = create_user(name="Admin6b", email="admin6b@test.com", role=UserRole.ADMIN, unit_id=unit.id)
    headers = auth_header_for_user(admin2)
    response = await client.post("/tickets", headers=headers, json={
        "unit_id": unit.id,
        "title": "Chamado Auditado",
        "description": "Teste de auditoria",
        "category": "electrical",
        "problem_type": "Falha na instalacao",
        "priority": "high",
        "severity": "medium",
    })
    assert response.status_code == 201

    logs = _get_audit_logs(db_session, "ticket_created")
    assert len(logs) >= 1
    assert logs[0].entity_type == "ticket"
    assert "category" in logs[0].metadata_json


# ── audit log for approval levels ────────────────────────────────────────────

@pytest.mark.anyio
async def test_audit_approval_level_created(client, create_user, auth_header_for_user, db_session):
    admin = create_user(name="Admin7", email="admin7@test.com", role=UserRole.ADMIN)
    headers = auth_header_for_user(admin)
    response = await client.post("/approval-levels", headers=headers, json={
        "name": "Alcada Auditada",
        "min_amount": "0",
        "max_amount": "5000",
        "allowed_roles": ["admin"],
        "is_active": True,
    })
    assert response.status_code == 201

    logs = _get_audit_logs(db_session, "approval_level_created")
    assert len(logs) >= 1
    assert logs[0].entity_type == "approval_level"


# ── audit log for suppliers ───────────────────────────────────────────────────

@pytest.mark.anyio
async def test_audit_supplier_created(client, create_user, auth_header_for_user, db_session):
    admin = create_user(name="Admin8", email="admin8@test.com", role=UserRole.ADMIN)
    headers = auth_header_for_user(admin)
    response = await client.post("/suppliers", headers=headers, json={
        "name": "Fornecedor Auditado",
        "document": "12345678000199",
        "phone": "11999999999",
        "email": "contato@fornecedor.com",
        "specialty": "Eletrica",
    })
    assert response.status_code == 201

    logs = _get_audit_logs(db_session, "supplier_created")
    assert len(logs) >= 1
    assert logs[0].entity_type == "supplier"
    assert "Fornecedor Auditado" in str(logs[0].metadata_json)


# ── audit log filters ─────────────────────────────────────────────────────────

@pytest.mark.anyio
async def test_audit_log_filter_by_action(client, create_user, auth_header_for_user, db_session):
    admin = create_user(name="Admin9", email="admin9@test.com", role=UserRole.ADMIN)
    headers = auth_header_for_user(admin)

    # Create something to generate an audit log
    await client.post("/users", headers=headers, json={
        "name": "User Filter",
        "email": "filter_target@test.com",
        "password": "pass12345",
        "role": "engineering",
    })

    response = await client.get("/audit-logs?action=user_created", headers=headers)
    assert response.status_code == 200
    data = response.json()
    for item in data["items"]:
        assert item["action"] == "user_created"


@pytest.mark.anyio
async def test_audit_log_filter_by_entity_type(client, create_user, auth_header_for_user, db_session):
    admin = create_user(name="Admin10", email="admin10@test.com", role=UserRole.ADMIN)
    headers = auth_header_for_user(admin)

    await client.post("/users", headers=headers, json={
        "name": "User Filter2",
        "email": "filter_et@test.com",
        "password": "pass12345",
        "role": "engineering",
    })

    response = await client.get("/audit-logs?entity_type=user", headers=headers)
    assert response.status_code == 200
    data = response.json()
    for item in data["items"]:
        assert item["entity_type"] == "user"


@pytest.mark.anyio
async def test_audit_log_paginated(client, create_user, auth_header_for_user):
    admin = create_user(name="Admin11", email="admin11@test.com", role=UserRole.ADMIN)
    headers = auth_header_for_user(admin)

    response = await client.get("/audit-logs?page=1&page_size=5", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert "page" in data
    assert "page_size" in data
    assert data["page_size"] == 5


@pytest.mark.anyio
async def test_audit_log_search(client, create_user, auth_header_for_user, db_session):
    admin = create_user(name="Admin Search", email="admin_srch@test.com", role=UserRole.ADMIN)
    headers = auth_header_for_user(admin)

    await client.post("/auth/login", json={"email": "admin_srch@test.com", "password": "admin123"})

    response = await client.get("/audit-logs?search=login_success", headers=headers)
    assert response.status_code == 200
    data = response.json()
    for item in data["items"]:
        assert "login" in item["action"]


# ── upload protection ─────────────────────────────────────────────────────────

def test_dangerous_extensions_set_not_empty():
    from app.services.attachment_service import _DANGEROUS_EXTENSIONS
    assert ".exe" in _DANGEROUS_EXTENSIONS
    assert ".sh" in _DANGEROUS_EXTENSIONS
    assert ".php" in _DANGEROUS_EXTENSIONS


@pytest.mark.anyio
async def test_upload_blocks_dangerous_extension(client, create_user, create_unit, auth_header_for_user, db_session):
    from app.models.ticket import Ticket
    from app.models.enums import TicketCategory, TicketStatus, PriorityLevel, TicketSeverity
    from datetime import datetime, timezone

    admin = create_user(name="Admin Up", email="admin_up@test.com", role=UserRole.ADMIN)
    unit = create_unit(code="UP-001", name="Unidade Up")
    admin2 = create_user(name="Admin Up2", email="admin_up2@test.com", role=UserRole.ADMIN, unit_id=unit.id)

    ticket = Ticket(
        unit_id=unit.id,
        opened_by_user_id=admin2.id,
        ticket_number="UP-0001",
        title="Ticket Upload",
        problem_type="Upload test",
        description="Test",
        category=TicketCategory.ELECTRICAL,
        priority=PriorityLevel.HIGH,
        severity=TicketSeverity.MEDIUM,
        status=TicketStatus.OPEN,
        opened_at=datetime.now(tz=timezone.utc),
    )
    db_session.add(ticket)
    db_session.commit()
    db_session.refresh(ticket)

    headers = auth_header_for_user(admin2)
    content = b"fake payload"
    files = {"file": ("malware.exe", content, "image/jpeg")}
    data = {"attachment_type": "photo"}

    response = await client.post(
        f"/tickets/{ticket.id}/attachments",
        headers=headers,
        files=files,
        data=data,
    )
    assert response.status_code == 422


@pytest.mark.anyio
async def test_upload_blocks_unsupported_mime(client, create_user, create_unit, auth_header_for_user, db_session):
    from app.models.ticket import Ticket
    from app.models.enums import TicketCategory, TicketStatus, PriorityLevel, TicketSeverity
    from datetime import datetime, timezone

    admin = create_user(name="Admin Mime", email="admin_mime@test.com", role=UserRole.ADMIN)
    unit = create_unit(code="MIME-001", name="Unidade Mime")
    admin2 = create_user(name="Admin Mime2", email="admin_mime2@test.com", role=UserRole.ADMIN, unit_id=unit.id)

    ticket = Ticket(
        unit_id=unit.id,
        opened_by_user_id=admin2.id,
        ticket_number="MIME-0001",
        title="Ticket Mime",
        problem_type="Mime test",
        description="Test",
        category=TicketCategory.ELECTRICAL,
        priority=PriorityLevel.HIGH,
        severity=TicketSeverity.MEDIUM,
        status=TicketStatus.OPEN,
        opened_at=datetime.now(tz=timezone.utc),
    )
    db_session.add(ticket)
    db_session.commit()
    db_session.refresh(ticket)

    headers = auth_header_for_user(admin2)
    content = b"<script>alert('xss')</script>"
    files = {"file": ("script.html", content, "text/html")}
    data = {"attachment_type": "photo"}

    response = await client.post(
        f"/tickets/{ticket.id}/attachments",
        headers=headers,
        files=files,
        data=data,
    )
    assert response.status_code == 422


# ── global error handler ──────────────────────────────────────────────────────

@pytest.mark.anyio
async def test_global_error_handler_returns_safe_500():
    import json
    from unittest.mock import MagicMock
    from app.core.errors import unhandled_exception_handler

    mock_request = MagicMock()
    mock_request.method = "GET"
    mock_request.url.path = "/test-path"

    exc = RuntimeError("internal details that must not leak")
    response = await unhandled_exception_handler(mock_request, exc)

    assert response.status_code == 500
    body = json.loads(response.body)
    assert "detail" in body
    assert "internal details" not in str(body)
    assert "RuntimeError" not in str(body)
    assert "Traceback" not in str(body)


# ── regression ────────────────────────────────────────────────────────────────

@pytest.mark.anyio
async def test_health_still_works(client):
    response = await client.get("/health/live")
    assert response.status_code == 200


@pytest.mark.anyio
async def test_login_still_works(client, create_user):
    create_user(name="Reg User", email="reg_login@test.com", role=UserRole.ADMIN, password="pass12345")
    response = await client.post("/auth/login", json={"email": "reg_login@test.com", "password": "pass12345"})
    assert response.status_code == 200
    assert "access_token" in response.json()


@pytest.mark.anyio
async def test_users_list_still_works(client, create_user, auth_header_for_user):
    admin = create_user(name="Reg Admin", email="reg_admin@test.com", role=UserRole.ADMIN)
    headers = auth_header_for_user(admin)
    response = await client.get("/users", headers=headers)
    assert response.status_code == 200


@pytest.mark.anyio
async def test_units_list_still_works(client, create_user, auth_header_for_user):
    admin = create_user(name="Reg Admin2", email="reg_admin2@test.com", role=UserRole.ADMIN)
    headers = auth_header_for_user(admin)
    response = await client.get("/units", headers=headers)
    assert response.status_code == 200
