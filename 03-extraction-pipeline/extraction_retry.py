import os
import anthropic
from dotenv import load_dotenv, find_dotenv
from models import ExtractionResult

load_dotenv(find_dotenv())
MODEL = os.getenv("ANTHROPIC_MODEL", "claude-haiku-4-5-20251001")
client = anthropic.Anthropic()  # legge ANTHROPIC_API_KEY dal .env

extraction_tool = {
    "name": "record_extracted_ticket",
    "description": "Registra i dati strutturati estratti dal testo di un ticket di service desk IT.",
    "input_schema": ExtractionResult.model_json_schema(),
}

SYSTEM_NULL_RULE = (
    "Estrai i dati strutturati dai ticket di service desk IT usando il tool fornito. "
    "Estrai solo ciò che è esplicitamente presente nel testo del ticket. "
    "Se un'informazione non è indicata nel testo, restituisci null per quel campo. "
    "Non inventare valori e non usare segnaposto come \"UNKNOWN\", \"N/D\" o simili."
    "Non calcolare né derivare valori. Se un prezzo unitario non è indicato "
    "esplicitamente, restituisci null anche quando è dato un totale: non dividere "
    "un totale per ottenere un prezzo unitario."
)
_FEWSHOT_EXAMPLES = [
    ('Per il team vendite serve un paio di licenze Project. g.bianchi@reti.it',
     '{"requester": {"employee_id": null, "email": "g.bianchi@reti.it", "name": null}, '
     '"request_type": "license_provisioning", "request_type_detail": null, '
     '"items": [{"product": "Project", "quantity": 2, "unit_cost_eur": null}], '
     '"stated_total_eur": null, "urgency": null}',
     "'un paio' è una quantità convenzionale (2), accettabile; prezzo unitario assente → null."),
    ('Richiesta 5 licenze Copilot, budget totale 250 EUR. l.verdi@reti.it',
     '{"requester": {"employee_id": null, "email": "l.verdi@reti.it", "name": null}, '
     '"request_type": "license_provisioning", "request_type_detail": null, '
     '"items": [{"product": "Copilot", "quantity": 5, "unit_cost_eur": null}], '
     '"stated_total_eur": 250.0, "urgency": null}',
     "Totale dichiarato (250); prezzo unitario NON indicato → null. Non dividere 250/5."),
    ('Richiedente | Prodotto | Qtà\nn.esposito@reti.it | Adobe Acrobat | 4',
     '{"requester": {"employee_id": null, "email": "n.esposito@reti.it", "name": null}, '
     '"request_type": "license_provisioning", "request_type_detail": null, '
     '"items": [{"product": "Adobe Acrobat", "quantity": 4, "unit_cost_eur": null}], '
     '"stated_total_eur": null, "urgency": null}',
     "Formato tabellare: stesse regole, stessa forma di output di un ticket in prosa."),
]

SYSTEM_FEWSHOT = SYSTEM_NULL_RULE + "\n\nEsempi di estrazione corretta:\n\n" + "\n\n".join(
    f'Ticket: "{t}"\nEstrazione: {out}\nNota: {nota}' for t, out, nota in _FEWSHOT_EXAMPLES
)

def call_model(messages, system=SYSTEM_FEWSHOT):
    response = client.messages.create(
        model=MODEL,
        max_tokens=1024,
        system=SYSTEM_NULL_RULE,
        tools=[extraction_tool],
        tool_choice={"type": "tool", "name": extraction_tool["name"]},
        messages=messages,
    )
    block = next((b for b in response.content if b.type == "tool_use"), None)
    return (block.id, block.input) if block else None


if __name__ == "__main__":
    from pipeline import run_extraction

    tickets = [
        ("SD-2001", "Da Mario Rossi (mario.rossi@reti.it): servono 2 licenze Visio, budget circa 200 EUR."),
        ("SD-1042", "Ciao, servono 3 licenze Copilot per il team marketing. Grazie, Anna"),
    ]
    for tid, raw in tickets:
        out = run_extraction(raw, tid, call_model, extraction_tool["name"])
        print(f"\n[{tid}] status={out.status}  attempts={out.attempts}")
        if out.ticket:
            print(out.ticket.model_dump_json(indent=2))
        for i in out.issues:
            print(f"   -> [{'R' if i.retryable else 'N'}] {i.field}: {i.message}")