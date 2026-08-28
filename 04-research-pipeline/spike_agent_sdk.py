"""Spike Agent SDK — EVIDENZA A PARTE: coordinator -> 1 subagent col VERO claude-agent-sdk.
Versione strumentata per il debug del primo run.

NON e' la pipeline dell'Es. 4 (quella e' su Messages API grezza, substrato B, deterministica).
Serve a toccare la superficie SDK dell'esame e a vedere dal vivo il TRAP Task->Agent.

Firme verificate sul pacchetto reale (claude-agent-sdk 0.2.147):
  from claude_agent_sdk import query, ClaudeAgentOptions, AgentDefinition, AssistantMessage
  - query(prompt=..., options=...) e' un generatore ASYNC
  - subagent = AgentDefinition(description=, prompt=, tools=, model=) in options.agents={nome: ...}
  - TRAP: i subagent si invocano col tool 'Agent' -> in allowed_tools. (Sull'ESAME la guida dice 'Task'.)

PREREQUISITI (lo lanci TU) — verificati sul pacchetto reale 0.2.147:
  1) pip install claude-agent-sdk   (Python 3.10+). Porta un CLI BUNDLATO
     (claude_agent_sdk/_bundled/claude): NON serve la CLI a parte via npm. Gira su Node.
  2) Auth: usa la tua Pro (login Claude Code) o ANTHROPIC_API_KEY se nell'ambiente.
  Errore atteso SENZA auth: ProcessError exit code 1.

permission_mode='bypassPermissions': in modalita' headless evita che il coordinator resti
BLOCCATO in silenzio su un prompt di permesso per un tool non in allowed_tools.
"""
import asyncio
from claude_agent_sdk import query, ClaudeAgentOptions, AgentDefinition, AssistantMessage

SUMMARIZER = AgentDefinition(
    description="Sintetizza un testo in una frase. Usalo per riassumere.",
    prompt="Sei un sintetizzatore: rispondi con UNA sola frase che riassume il testo dato.",
    tools=[],
    model="haiku",
)

OPTIONS = ClaudeAgentOptions(
    allowed_tools=["Agent"],              # <-- IL TRAP: 'Agent' (non 'Task')
    agents={"summarizer": SUMMARIZER},
    model="haiku",
    max_turns=4,
    permission_mode="bypassPermissions",  # headless: niente blocchi muti sui permessi
)

PROMPT = ("Usa il subagent 'summarizer' per riassumere in una frase: "
          "'Il lavoro da remoto mostra effetti contrastanti sulla produttivita', "
          "a seconda di come la si misura e dell'anno dello studio.'")


async def main():
    print(">> avvio query (attendo i messaggi in streaming)...", flush=True)
    saw_delegation = False
    final = None
    count = 0
    try:
        async for message in query(prompt=PROMPT, options=OPTIONS):
            count += 1
            print(f"   [msg {count}] {type(message).__name__}", flush=True)
            if isinstance(message, AssistantMessage):
                for block in getattr(message, "content", []):
                    name = getattr(block, "name", None)
                    if name:
                        print(f"        tool_use -> {name}", flush=True)
                    if name in ("Agent", "Task"):
                        saw_delegation = True
            if hasattr(message, "result") and getattr(message, "result", None):
                final = message.result
    except Exception as e:
        print(f"!! ECCEZIONE {type(e).__name__}: {e}", flush=True)
        raise

    print(f"\nMessaggi ricevuti: {count}", flush=True)
    print("Delega a subagent avvenuta:", saw_delegation, flush=True)
    print("Risultato finale:", final, flush=True)


if __name__ == "__main__":
    asyncio.run(main())