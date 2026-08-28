"""Subagent di ricerca (Es. 4) — la prima 'testa vera' (chiamata Haiku reale).

Principi incardinati qui:
- CONTESTO ESPLICITO (Card 2 / Task 1.3): il subagent non eredita nulla. Tutto cio' che
  gli serve viene costruito nel prompt da build_prompt(). L'unico canale e' il prompt.
- PROVENANCE AUTOREVOLE (Card 18 / Task 5.6): il modello produce SOLO la parte cognitiva
  (claim + excerpt). Fonte, riferimento e data li timbra il CODICE dal fixture: il tool non
  espone nemmeno quei campi, quindi il modello e' strutturalmente incapace di fabbricarli.
- TRE ESITI (Card 5 / Task 5.3): timeout -> SubagentError; nessuna fonte -> vuoto valido
  (findings=[], error=None); fonti -> findings. Nessuna chiamata sprecata su vuoto/timeout.

Deviazione voluta dalle tue convenzioni dell'Es. 3: il client anthropic e' inizializzato
in modo LAZY (non a import-time), cosi' questo modulo si importa e si testa senza API key.
"""
import os
import anthropic
from sources import retrieve, SourceTimeout, TOPIC, Source
from models import Finding, SubagentResult, SubagentError, FailureType

MODEL = os.getenv("ANTHROPIC_MODEL", "claude-haiku-4-5-20251001")

# Il tool espone SOLO la parte cognitiva. Niente campi di provenance -> niente da inventare.
FINDING_TOOL = {
    "name": "record_finding",
    "description": ("Registra il finding estratto dall'UNICA fonte fornita: una sintesi (claim) "
                    "e un frammento LETTERALE dal testo della fonte a supporto (evidence)."),
    "input_schema": {
        "type": "object",
        "properties": {
            "claim": {"type": "string",
                      "description": "Sintesi in una frase di cio' che la fonte afferma sul sottotema."},
            "evidence_excerpt": {"type": "string",
                      "description": "Frammento LETTERALE preso dal testo della fonte, a supporto del claim."},
        },
        "required": ["claim", "evidence_excerpt"],
    },
}

SUBAGENT_SYSTEM = (
    "Sei un subagent di ricerca. Analizzi ESCLUSIVAMENTE l'unica fonte che ti viene passata, "
    "sul sottotema indicato. Produci un solo finding tramite il tool: un claim sintetico e un "
    "excerpt LETTERALE dal testo. Non citare altre fonti, non aggiungere dati non presenti nel testo."
)


def build_prompt(topic: str, subtopic: str, source: Source) -> tuple[str, str]:
    """Contesto ESPLICITO: il subagent riceve tutto qui, non eredita niente.
    Nota: NON passo nome/ref/data della fonte — non gli servono (la provenance la timbra il codice)
    e ometterle toglie ogni tentazione di ri-scriverle sbagliate."""
    user = (f"TOPIC DI RICERCA: {topic}\n"
            f"SOTTOTEMA ASSEGNATO: {subtopic}\n\n"
            f"FONTE (unica):\n{source.text}")
    return SUBAGENT_SYSTEM, user


def run_subagent(agent: str, channel: str, subtopic: str, topic: str, call) -> SubagentResult:
    """Orchestrazione pura del subagent. 'call(system, user) -> {"claim","evidence_excerpt"}'
    e' iniettata: stub deterministico nei test, Haiku vero in produzione (_call_haiku).
    NON tocca l'SDK -> interamente testabile senza API."""
    try:
        sources = retrieve(channel, subtopic)
    except SourceTimeout as e:
        # fallimento d'accesso -> errore STRUTTURATO, niente chiamata sprecata
        return SubagentResult(agent=agent, subtopic=subtopic,
            error=SubagentError(failure_type=FailureType.timeout,
                                attempted_query=f"{channel}:{subtopic}",
                                detail=str(e)))
    # nessuna fonte -> vuoto valido: il loop non gira, findings resta [], niente chiamata
    findings: list[Finding] = []
    for s in sources:
        system, user = build_prompt(topic, subtopic, s)
        out = call(system, user)                       # <- unica riga cognitiva (modello)
        findings.append(Finding(
            claim=out["claim"],
            evidence_excerpt=out["evidence_excerpt"],
            source_name=s.name,                        # provenance AUTOREVOLE dal fixture
            source_ref=s.ref,
            published_date=s.published_date,
        ))
    return SubagentResult(agent=agent, subtopic=subtopic, findings=findings)


# --- chiamata reale a Haiku: la lanci TU (serve .env + credito). Mirror di extraction.py. ---
_client = None

def _get_client():
    global _client
    if _client is None:
        from dotenv import load_dotenv
        load_dotenv()
        _client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    return _client

def _call_haiku(system: str, user: str) -> dict:
    response = _get_client().messages.create(
        model=MODEL,
        max_tokens=512,
        system=system,
        tools=[FINDING_TOOL],
        tool_choice={"type": "tool", "name": "record_finding"},
        messages=[{"role": "user", "content": user}],
        extra_body={"temperature": 0},
    )
    tool_use = next((b for b in response.content if b.type == "tool_use"), None)
    if tool_use is None:                               # con tool forzato non dovrebbe capitare
        return {"claim": "", "evidence_excerpt": ""}
    return tool_use.input


if __name__ == "__main__":
    # CHIAMATA REALE (la lanci tu). Un subagent, una fonte, per vedere la 'testa' girare davvero.
    r = run_subagent("web_researcher", "web", "productivity_metrics", TOPIC, _call_haiku)
    print(f"agent={r.agent}  subtopic={r.subtopic}  error={r.error}")
    for f in r.findings:
        print(f"\n  claim   : {f.claim}")
        print(f"  evidence: {f.evidence_excerpt}")
        print(f"  fonte   : {f.source_name} ({f.source_ref}) {f.published_date}")