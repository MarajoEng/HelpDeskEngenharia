from enum import Enum


class UserRole(str, Enum):
    ADMIN = "admin"
    MANAGER = "manager"
    ENGINEERING = "engineering"
    DIRECTOR = "director"
    SUPPLIER = "supplier"


class TicketStatus(str, Enum):
    OPEN = "open"
    TRIAGE = "triage"
    WAITING_APPROVAL = "waiting_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    IN_PROGRESS = "in_progress"
    WAITING_SUPPLIER = "waiting_supplier"
    WAITING_UNIT = "waiting_unit"
    RESOLVED = "resolved"
    CLOSED = "closed"
    CANCELED = "canceled"


class TicketCategory(str, Enum):
    FUEL_PUMP = "fuel_pump"
    FUEL_NOZZLE = "fuel_nozzle"
    ELECTRICAL = "electrical"
    PLUMBING = "plumbing"
    LEAK = "leak"
    STRUCTURE = "structure"
    ROOF = "roof"
    PAVEMENT = "pavement"
    ENVIRONMENTAL_RISK = "environmental_risk"
    OTHER = "other"


class PriorityLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
