from decimal import Decimal
import pytest
from sqlalchemy import select

from app.models.approval_level import ApprovalLevel
from app.models.supplier import Supplier
from app.models.ticket import Ticket
from app.models.unit import Unit
from app.models.user import User
from scripts.seed_demo import (
    seed_approval_levels,
    seed_suppliers,
    seed_tickets,
    seed_units,
    seed_users,
)


@pytest.fixture
def empty_db(db_session):
    # Ensure tables are clean before running the seed (since it relies on empty or existing states)
    db_session.execute(Ticket.__table__.delete())
    db_session.execute(Supplier.__table__.delete())
    db_session.execute(User.__table__.delete())
    db_session.execute(Unit.__table__.delete())
    db_session.execute(ApprovalLevel.__table__.delete())
    db_session.commit()
    return db_session


def test_seed_demo_idempotent(empty_db):
    session = empty_db

    # First run
    levels = seed_approval_levels(session)
    assert len(levels) == 3
    
    units = seed_units(session)
    assert len(units) >= 10
    
    users = seed_users(session, units)
    assert len(users) >= 5
    
    suppliers = seed_suppliers(session)
    assert len(suppliers) >= 5
    
    seed_tickets(session, units, users, suppliers, levels)
    session.commit()

    # Count after first run
    c_levels = session.scalar(select(ApprovalLevel).with_only_columns(ApprovalLevel.id))
    c_units = session.scalar(select(Unit).with_only_columns(Unit.id))
    c_users = session.scalar(select(User).with_only_columns(User.id))
    c_suppliers = session.scalar(select(Supplier).with_only_columns(Supplier.id))
    c_tickets = session.scalar(select(Ticket).with_only_columns(Ticket.id))

    count_levels = len(session.scalars(select(ApprovalLevel)).all())
    count_units = len(session.scalars(select(Unit)).all())
    count_users = len(session.scalars(select(User)).all())
    count_suppliers = len(session.scalars(select(Supplier)).all())
    count_tickets = len(session.scalars(select(Ticket)).all())

    # Second run (should be idempotent)
    levels2 = seed_approval_levels(session)
    units2 = seed_units(session)
    users2 = seed_users(session, units2)
    suppliers2 = seed_suppliers(session)
    seed_tickets(session, units2, users2, suppliers2, levels2)
    session.commit()

    # Assert counts remain the same
    assert count_levels == len(session.scalars(select(ApprovalLevel)).all())
    assert count_units == len(session.scalars(select(Unit)).all())
    assert count_users == len(session.scalars(select(User)).all())
    assert count_suppliers == len(session.scalars(select(Supplier)).all())
    assert count_tickets == len(session.scalars(select(Ticket)).all())

    # Some ticket sanity checks
    # Assert ticket with alert
    t4 = session.scalar(select(Ticket).where(Ticket.ticket_number.like("%-000004")))
    assert t4 is not None
    assert t4.requires_approval is True
    assert t4.approved_cost == Decimal("4500.00")
    assert len(t4.alerts) > 0
