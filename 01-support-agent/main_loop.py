import os
import json
from dotenv import load_dotenv
import anthropic
from tools import TOOLS, TOOL_FUNCTIONS   # ora serve anche il registro

load_dotenv()
client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

SYSTEM = (
    "Sei un agente di service desk IT interno. "
    "Rispondi sempre in italiano, in modo conciso. "
    "Usa i tool per verificare dipendenti, catalogo, entitlement e provisioning."
)

MAX_TURNS = 10   # rete di sicurezza, NON la condizione di uscita

def run_agent(user_message):
    messages = [{"role": "user", "content": user_message}]

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
            if block.type == "tool_use":
                result = TOOL_FUNCTIONS[block.name](**block.input)
                print(f"  [turno {turn}] {block.name}{block.input} -> {result}")
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": json.dumps(result),
                })

        # (c) restituisci tutti i risultati in un unico messaggio 'user'
        messages.append({"role": "user", "content": tool_results})

    print("[Interrotto: superato il numero massimo di turni]")


if __name__ == "__main__":
    run_agent("Per alice@company.com, mi dici di Power BI Pro?")