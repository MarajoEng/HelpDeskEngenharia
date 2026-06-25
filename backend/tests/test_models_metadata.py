from sqlalchemy import Enum as SqlEnum, create_engine, inspect

from app.models import Base
from app.models.enums import ApprovalStatus, TicketSeverity


EXPECTED_TABLES = {
    "approvals",
    "suppliers",
    "ticket_attachments",
    "ticket_history",
    "tickets",
    "units",
    "users",
}


def test_metadata_registers_expected_tables() -> None:
    assert EXPECTED_TABLES.issubset(Base.metadata.tables.keys())


def test_metadata_creates_schema_on_sqlite_for_validation() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:")

    Base.metadata.create_all(bind=engine)

    inspector = inspect(engine)
    assert EXPECTED_TABLES.issubset(inspector.get_table_names())


def test_metadata_exposes_contract_enums_on_critical_columns() -> None:
    ticket_severity = Base.metadata.tables["tickets"].c["severity"].type
    approval_status = Base.metadata.tables["approvals"].c["status"].type

    assert isinstance(ticket_severity, SqlEnum)
    assert ticket_severity.enum_class is TicketSeverity
    assert isinstance(approval_status, SqlEnum)
    assert approval_status.enum_class is ApprovalStatus
