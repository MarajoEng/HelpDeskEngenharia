from decimal import Decimal
import pytest
from sqlalchemy import select

from app.models.approval_level import ApprovalLevel
from app.models.supplier import Supplier
from app.models.ticket_category import TicketCategoryConfig
from app.models.ticket_category_type import TicketCategoryTypeLink
from app.models.ticket_priority import TicketPriorityConfig
from app.models.ticket_subcategory import TicketSubcategoryConfig
from app.models.ticket import Ticket
from app.models.ticket_type import TicketTypeConfig
from app.models.unit import Unit
from app.models.user import User
from scripts.seed_demo import (
    seed_approval_levels,
    seed_suppliers,
    seed_ticket_configuration,
    seed_tickets,
    seed_units,
    seed_users,
)


@pytest.fixture
def empty_db(db_session):
    # Ensure tables are clean before running the seed (since it relies on empty or existing states)
    db_session.execute(Ticket.__table__.delete())
    db_session.execute(Supplier.__table__.delete())
    db_session.execute(TicketCategoryTypeLink.__table__.delete())
    db_session.execute(TicketSubcategoryConfig.__table__.delete())
    db_session.execute(TicketCategoryConfig.__table__.delete())
    db_session.execute(TicketTypeConfig.__table__.delete())
    db_session.execute(TicketPriorityConfig.__table__.delete())
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

    ticket_configuration = seed_ticket_configuration(session)
    assert len(ticket_configuration["categories"]) >= 10
    assert len(ticket_configuration["subcategories"]) >= 10
    assert len(ticket_configuration["types"]) >= 5
    assert len(ticket_configuration["priorities"]) >= 4

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
    count_ticket_categories = len(session.scalars(select(TicketCategoryConfig)).all())
    count_ticket_subcategories = len(session.scalars(select(TicketSubcategoryConfig)).all())
    count_ticket_types = len(session.scalars(select(TicketTypeConfig)).all())
    count_ticket_priorities = len(session.scalars(select(TicketPriorityConfig)).all())
    count_units = len(session.scalars(select(Unit)).all())
    count_users = len(session.scalars(select(User)).all())
    count_suppliers = len(session.scalars(select(Supplier)).all())
    count_tickets = len(session.scalars(select(Ticket)).all())

    # Second run (should be idempotent)
    levels2 = seed_approval_levels(session)
    seed_ticket_configuration(session)
    units2 = seed_units(session)
    users2 = seed_users(session, units2)
    suppliers2 = seed_suppliers(session)
    seed_tickets(session, units2, users2, suppliers2, levels2)
    session.commit()

    # Assert counts remain the same
    assert count_levels == len(session.scalars(select(ApprovalLevel)).all())
    assert count_ticket_categories == len(session.scalars(select(TicketCategoryConfig)).all())
    assert count_ticket_subcategories == len(session.scalars(select(TicketSubcategoryConfig)).all())
    assert count_ticket_types == len(session.scalars(select(TicketTypeConfig)).all())
    assert count_ticket_priorities == len(session.scalars(select(TicketPriorityConfig)).all())
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
