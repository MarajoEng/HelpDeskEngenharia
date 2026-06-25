from app.models.enums import PriorityLevel, TicketCategory, TicketStatus, UserRole


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
