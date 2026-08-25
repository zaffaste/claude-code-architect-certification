import os
import json
from dotenv import load_dotenv
import anthropic
from tools import TOOLS, TOOL_FUNCTIONS   # ora serve anche il registro
from stubs import lookup_product_catalog   # la guardia risolve il costo da sé

load_dotenv()
client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

SPEND_LIMIT = 500

def check_provisioning_allowed(tool_input, verified_employees):
    """Decide se provision_access può procedere. Ritorna (allowed, reason)."""
    employee_id = tool_input.get("employee_id")
    product = tool_input.get("product")
    quantity = tool_input.get("quantity", 1)

    # Regola 1 — identità verificata e attiva in QUESTA sessione
    emp = verified_employees.get(employee_id)
    if emp is None:
        return False, (f"Provisioning negato: identità '{employee_id}' non "
                       f"verificata in questa sessione. Chiama prima get_employee.")
    if not emp.get("active", False):
        return False, f"Provisioning negato: dipendente '{employee_id}' non attivo."

    # Regola 2 — soglia di spesa, con costo risolto in autonomia dal catalogo
    catalog = lookup_product_catalog(product)
    if not catalog.get("found"):
        return False, f"Provisioning negato: prodotto '{product}' non a catalogo."
    cost = quantity * catalog["value"]["cost_per_seat"]
    if cost > SPEND_LIMIT:
        return False, (f"Provisioning di {quantity}x {product} = €{cost}, oltre il "
                       f"limite di €{SPEND_LIMIT}. Richiede approvazione umana.")

    return True, ""

SYSTEM = """Sei un agente di service desk IT interno. Rispondi sempre in italiano, in modo conciso.

Usi i tool per verificare dipendenti, catalogo, entitlement e provisioning.

Se un messaggio contiene più richieste distinte, gestiscile una per una.

Escala a un operatore umano tramite il tool escalate_to_human quando:
- l'utente chiede esplicitamente un umano;
- la richiesta è fuori dallo scope dei tuoi tool (es. problemi di rete, VPN, hardware): non improvvisare una soluzione, inoltra;
- un'operazione è bloccata o richiede approvazione (es. spesa oltre soglia).

Non inventare informazioni o procedure che i tuoi tool non coprono."""

MAX_TURNS = 10   # rete di sicurezza, NON la condizione di uscita

def run_agent(user_message):
    messages = [{"role": "user", "content": user_message}]
    verified_employees = {}

    for turn in range(1, MAX_TURNS + 1):
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=1024,
            system=SYSTEM,
            tools=TOOLS,
            messages=messages,
        )

        # Il modello continua a lavorare SOLO se chiede tool.
        # Qualsiasi altro stop_reason (end_turn, ecc.) = ha finito -> esci.
        if response.stop_reason != "tool_use":
            for block in response.content:
                if block.type == "text":
                    print("RISPOSTA:", block.text)
            return

        # (a) registra nel dialogo ciò che il modello ha chiesto
        messages.append({"role": "assistant", "content": response.content})

        # (b) esegui OGNI tool richiesto in questo turno (possono essere più d'uno)
        tool_results = []
        for block in response.content:
            if block.type != "tool_use":
                continue

            # ENFORCEMENT: solo provision_access passa dalla guardia
            if block.name == "provision_access":
                allowed, reason = check_provisioning_allowed(block.input, verified_employees)
                if not allowed:
                    print(f"  [turno {turn}] BLOCCATO provision_access{block.input}: {reason}")
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": reason,
                        "is_error": True,          # segnala al modello che NON è andata
                    })
                    continue                       # il tool NON viene eseguito

            # esecuzione normale (lookup, o provision approvato)
            result = TOOL_FUNCTIONS[block.name](**block.input)
            print(f"  [turno {turn}] {block.name}{block.input} -> {result}")

            # STATO DI SESSIONE: registra chi è verificato e attivo
            if (block.name == "get_employee"
                    and result.get("found")
                    and result["value"].get("active")):
                verified_employees[result["value"]["employee_id"]] = result["value"]

            tool_results.append({
                "type": "tool_result",
                "tool_use_id": block.id,
                "content": json.dumps(result),
            })

        # (c) restituisci tutti i risultati in un unico messaggio 'user'
        messages.append({"role": "user", "content": tool_results})

    print("[Interrotto: superato il numero massimo di turni]")


if __name__ == "__main__":
    # run_agent("Per alice@company.com, mi dici di Power BI Pro?")
    # run_agent("Provisiona 15 licenze Copilot per alice@company.com")
    # run_agent("Provisiona 5 licenze Power BI Pro per alice@company.com")
    run_agent(
        "Ciao, per alice@company.com ho tre domande: dimmi se ha Power BI Pro; "
        "la VPN non le si ocnnette da stamattina; assegnale 15 licenze Copilot."
    )