from app.models.enums import (
    ApprovalStatus,
    PriorityLevel,
    TicketCategory,
    TicketSeverity,
    TicketStatus,
    UserRole,
)


def test_user_roles_match_expected_contract() -> None:
    assert [role.value for role in UserRole] == [
        "admin",
        "manager",
        "engineering",
        "director",
        "supplier",
    ]


def test_ticket_statuses_match_expected_contract() -> None:
    assert [status.value for status in TicketStatus] == [
        "open",
        "triage",
        "waiting_approval",
        "approved",
        "rejected",
        "in_progress",
        "waiting_supplier",
        "waiting_unit",
        "resolved",
        "closed",
        "canceled",
    ]


def test_ticket_categories_match_expected_contract() -> None:
    assert [category.value for category in TicketCategory] == [
        "fuel_pump",
        "fuel_nozzle",
        "electrical",
        "plumbing",
        "leak",
        "structure",
        "roof",
        "pavement",
        "environmental_risk",
        "other",
    ]


def test_priorities_match_expected_contract() -> None:
    assert [priority.value for priority in PriorityLevel] == [
        "low",
        "medium",
        "high",
        "critical",
    ]


def test_ticket_severities_match_expected_contract() -> None:
    assert [severity.value for severity in TicketSeverity] == [
        "low",
        "medium",
        "high",
        "critical",
    ]


def test_approval_statuses_match_expected_contract() -> None:
    assert [status.value for status in ApprovalStatus] == [
        "pending",
        "approved",
        "rejected",
        "canceled",
    ]
