from models import Ticket
from pydantic import ValidationError

# Caso 1: il ticket sorgente NON conteneva employee_id, costi, urgenza.
# Il modello (correttamente) emette null su quei campi invece di inventarli.
ok = Ticket.model_validate({
    "ticket_id": "SD-1042",
    "raw_text": "Ciao, servono 3 licenze Copilot per il team marketing. Grazie, Anna",
    "requester": {"employee_id": None, "email": None, "name": "Anna"},
    "request_type": "license_provisioning",
    "request_type_detail": None,
    "items": [{"product": "M365 Copilot", "quantity": 3, "unit_cost_eur": None}],
    "stated_total_eur": None,
    "urgency": None,
})
print("valido:", ok.model_dump())

# Caso 2: il modello ha OMESSO una chiave invece di mettere null.
# Vogliamo che questo FALLISCA: è l'errore strutturale che lo Step 2 ritenterà.
try:
    Ticket.model_validate({
        "ticket_id": "SD-1042", "raw_text": "...",
        "requester": {"email": None, "name": "Anna"},   # employee_id assente
        "request_type": "license_provisioning", "request_type_detail": None,
        "items": [], "stated_total_eur": None, "urgency": None,
    })
    print("ERRORE: doveva fallire")
except ValidationError as e:
    print("chiave omessa respinta:", [x["loc"] for x in e.errors()])