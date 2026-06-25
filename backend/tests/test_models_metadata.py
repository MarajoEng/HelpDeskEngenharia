from sqlalchemy import create_engine, inspect

from app.models import Base


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
