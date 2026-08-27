from enum import Enum
from pydantic import BaseModel


class RequestType(str, Enum):
    license_provisioning = "license_provisioning"
    hardware = "hardware"
    access = "access"
    vpn = "vpn"
    other = "other"
    unclear = "unclear"


class Urgency(str, Enum):
    low = "low"
    normal = "normal"
    high = "high"


class Requester(BaseModel):
    employee_id: str | None
    email: str | None
    name: str | None


class LineItem(BaseModel):
    product: str
    quantity: int | None
    unit_cost_eur: float | None


class ExtractionResult(BaseModel):
    """Solo ciò che il modello deve LEGGERE dal testo del ticket."""
    requester: Requester
    request_type: RequestType
    request_type_detail: str | None
    items: list[LineItem]
    stated_total_eur: float | None
    urgency: Urgency | None


class Ticket(ExtractionResult):
    """Record completo = estrazione + metadati che possediamo già."""
    ticket_id: str
    raw_text: str