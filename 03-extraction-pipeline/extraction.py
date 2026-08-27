import os
import json
import anthropic
from models import ExtractionResult, Ticket
from dotenv import load_dotenv

load_dotenv()
MODEL = os.getenv("ANTHROPIC_MODEL", "claude-haiku-4-5-20251001")  # verifica la stringa esatta nella tua Console, sezione Models
client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

extraction_tool = {
    "name": "record_extracted_ticket",
    "description": "Registra i dati strutturati estratti dal testo di un ticket di service desk IT.",
    "input_schema": ExtractionResult.model_json_schema(),
}

# Baseline volutamente neutro: NESSUNA istruzione sui null. Vogliamo vedere se lo
# schema nullable, da solo, basta a impedire che il modello inventi i dati assenti.
SYSTEM_BASELINE = "Estrai i dati strutturati dai ticket di service desk IT usando il tool fornito."
SYSTEM_NULL_RULE = (
    "Estrai i dati strutturati dai ticket di service desk IT usando il tool fornito. "
    "Estrai solo ciò che è esplicitamente presente nel testo del ticket. "
    "Se un'informazione non è indicata nel testo, restituisci null per quel campo. "
    "Non inventare valori e non usare segnaposto come \"UNKNOWN\", \"N/D\" o simili."
)


def extract(raw_text: str, system: str = SYSTEM_BASELINE) -> dict | None:
    response = client.messages.create(
        model=MODEL,
        max_tokens=1024,
        system=system,
        tools=[extraction_tool],
        tool_choice={"type": "tool", "name": "record_extracted_ticket"},
        messages=[{"role": "user", "content": raw_text}],
        extra_body={"temperature": 0},
    )
    # print("stop_reason:", response.stop_reason)
    tool_use = next((b for b in response.content if b.type == "tool_use"), None)
    if tool_use is None:
        # print("nessun blocco tool_use; contenuto:", response.content)
        return None
    return tool_use.input


# if __name__ == "__main__":
#     raw = "Ciao, servono 3 licenze Copilot per il team marketing. Grazie, Anna"

#     data = extract(raw)
#     print("\n--- input grezzo del modello ---")
#     print(json.dumps(data, indent=2, ensure_ascii=False))

#     result = ExtractionResult.model_validate(data)
#     ticket = Ticket(ticket_id="SD-1042", raw_text=raw, **result.model_dump())
#     print("\n--- record completo (Ticket) ---")
#     print(ticket.model_dump_json(indent=2))

# if __name__ == "__main__":
#     raw = "Ciao, servono 3 licenze Copilot per il team marketing. Grazie, Anna"
#     for label, system in [
#         ("BASELINE — nessuna regola", SYSTEM_BASELINE),
#         ("VARIANTE — regola null esplicita", SYSTEM_NULL_RULE),
#     ]:
#         print(f"\n===== {label} =====")
#         data = extract(raw, system)
#         print(json.dumps(data, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    raw = "Ciao, servono 3 licenze Copilot per il team marketing. Grazie, Anna"
    # Ground truth per QUESTO ticket: employee_id ed email non sono nel testo -> attesi null.
    EXPECTED_NULL = ["employee_id", "email"]
    N = 10

    for label, system in [
        ("BASELINE", SYSTEM_BASELINE),
        ("NULL_RULE", SYSTEM_NULL_RULE),
    ]:
        filled = {f: 0 for f in EXPECTED_NULL}      # quante run hanno riempito il campo
        seen = {f: set() for f in EXPECTED_NULL}    # quali valori sono comparsi
        no_extraction = 0

        for _ in range(N):
            data = extract(raw, system)
            if data is None:
                no_extraction += 1
                continue
            req = data.get("requester", {})
            for f in EXPECTED_NULL:
                if req.get(f) is not None:
                    filled[f] += 1
                    seen[f].add(req[f])

        print(f"\n===== {label} — {N} run =====")
        if no_extraction:
            print(f"  chiamate senza estrazione (no tool_use): {no_extraction}/{N}")
        for f in EXPECTED_NULL:
            line = f"  {f}: riempito (!=null) {filled[f]}/{N}"
            if seen[f]:
                line += f"   valori visti: {sorted(seen[f])}"
            print(line)