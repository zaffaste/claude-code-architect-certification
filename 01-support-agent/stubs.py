"""Stub di sistemi esterni: dati finti, hardcoded, in memoria."""

_EMPLOYEES = {
    "alice@company.com": {
        "employee_id": "E001",
        "name": "Alice Rossi",
        "email": "alice@company.com",
        "active": True,
    },
    "bob@company.com": {
        "employee_id": "E002",
        "name": "Bob Bianchi",
        "email": "bob@company.com",
        "active": True,
    },
    "carol@company.com": {
        "employee_id": "E003",
        "name": "Carol Verdi",
        "email": "carol@company.com",
        "active": False,
    },
    # "dave@company.com" non esiste: usata per il caso "non trovato".
}

_PRODUCT_CATALOG = {
    # cost_per_seat = 40: su 15 seat sfora la soglia dei 500€ (40 * 15 = 600).
    "Copilot": {"cost_per_seat": 40, "seats_available": 100},
    # cost_per_seat basso: resta sotto soglia anche su seat numerosi (contro-caso).
    "Power BI Pro": {"cost_per_seat": 10, "seats_available": 50},
    "Visio Plan 2": {"cost_per_seat": 15, "seats_available": 30},
    "Teams Premium": {"cost_per_seat": 7, "seats_available": 200},
}

_ENTITLEMENTS = {
    # Coppia già assegnata: fa emergere il no-op quando viene richiesta di nuovo.
    ("E001", "Copilot"): "assigned",
    ("E002", "Copilot"): "not_assigned",
    ("E001", "Power BI Pro"): "pending",
}


def get_employee(email):
    employee = _EMPLOYEES.get(email)
    if employee is None:
        return {"found": False}
    return {"found": True, "value": employee}


def lookup_product_catalog(product):
    if product not in _PRODUCT_CATALOG:
        return {"found": False}
    return {"found": True, "value": _PRODUCT_CATALOG[product]}


def check_entitlement(employee_id, product):
    status = _ENTITLEMENTS.get((employee_id, product))
    if status is None:
        return {"found": False}
    return {"found": True, "value": status}


def provision_access(employee_id, product, quantity=1):
    return {"status": "provisioned", "employee_id": employee_id, "product": product, "quantity": quantity}

def escalate_to_human(reason, summary, employee_id=None, product=None):
    return {
        "status": "escalated",
        "ticket_id": "ESC-1001",     # id fisso: è uno stub deterministico
        "reason": reason,
        "summary": summary,
        "employee_id": employee_id,
        "product": product,
    }
