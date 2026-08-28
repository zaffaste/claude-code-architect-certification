"""Sintesi della research pipeline (Es. 4) — il componente piu' 'da esame' (Task 5.6).

Principio (come subagents.py, applicato al conflitto):
- Il modello NON possiede le fonti e NON puo' scegliere un vincitore. Il tool judge_subtopic
  gli lascia dire SOLO status (established/contested) + note. Le posizioni in conflitto le
  ricostruisce il CODICE dai Finding autorevoli -> entrambi i valori sopravvivono per costruzione.
- La DATA tipizzata (scelta in models.py) serve qui: valori opposti con date diverse possono
  essere una DIFFERENZA TEMPORALE, non una contraddizione -> lo si annota.
- 1 finding  -> established senza chiamata (niente da riconciliare).
  >=2 findings -> unica chiamata reale (l'unico vero giudizio).
- I coverage_gaps passano dritti dal bundle.
"""
from enum import Enum
from models import Finding, SubagentResult, SynthesisReport, ContestedClaim
from subagents import MODEL, _get_client


class ClaimStatus(str, Enum):
    established = "established"
    contested = "contested"


# Il tool espone SOLO il verdetto. Niente campi per le fonti -> impossibile scartarne una.
SYNTHESIS_TOOL = {
    "name": "judge_subtopic",
    "description": ("Giudica se i findings sullo stesso sottotema sono concordi (established) o in "
                    "conflitto (contested), e spiega in una nota. NON elencare le fonti: le gestisce il codice."),
    "input_schema": {
        "type": "object",
        "properties": {
            "status": {"type": "string", "enum": [s.value for s in ClaimStatus]},
            "note": {"type": "string",
                     "description": ("Spiegazione breve. Se i valori divergono ma le date sono diverse, "
                                     "valuta se e' una differenza temporale piu' che una contraddizione.")},
        },
        "required": ["status", "note"],
    },
}

SYNTH_SYSTEM = (
    "Sei l'agente di sintesi. Ricevi piu' findings sullo STESSO sottotema, ciascuno con la sua data. "
    "Giudica se sono concordi (established) o in conflitto (contested) e spiega in una nota breve. "
    "Se i valori divergono ma le date sono diverse, valuta se e' una DIFFERENZA TEMPORALE piu' che una "
    "contraddizione, e scrivilo. NON elencare le fonti: le gestisce il codice."
)


def build_synth_prompt(subtopic: str, findings: list[Finding]) -> tuple[str, str]:
    """Al modello passo SOLO data + claim: basta per giudicare conflitto/temporalita', e senza
    identificativi di fonte non puo' nemmeno 'scegliere' una fonte."""
    lines = [f"- [{f.published_date}] {f.claim}" for f in findings]
    return SYNTH_SYSTEM, f"SOTTOTEMA: {subtopic}\nFINDINGS:\n" + "\n".join(lines)


def synthesize(results: list[SubagentResult], coverage_gaps: list[str], call) -> SynthesisReport:
    """Raggruppa i findings per sottotema (results ha gia' .subtopic) e costruisce il report.
    'call(system, user) -> {"status","note"}' iniettabile: fake nei test, Haiku vero in produzione."""
    by_subtopic: dict[str, list[Finding]] = {}
    for r in results:
        by_subtopic.setdefault(r.subtopic, []).extend(r.findings)

    report = SynthesisReport(coverage_gaps=list(coverage_gaps))
    for subtopic, findings in by_subtopic.items():
        if not findings:
            continue                                   # 0 findings -> gia' un coverage gap
        if len(findings) == 1:
            report.established.append(findings[0])     # niente da riconciliare, NESSUNA chiamata
            continue
        verdict = call(*build_synth_prompt(subtopic, findings))   # unico vero giudizio
        if verdict["status"] == ClaimStatus.contested.value:
            # entrambi i valori preservati con attribuzione: le posizioni le tiene il CODICE
            report.contested.append(ContestedClaim(topic=subtopic, positions=findings, note=verdict["note"]))
        else:
            report.established.extend(findings)        # concordi
    return report


# --- Chiamata reale della sintesi: la lanci TU. ---
def _call_synth_haiku(system: str, user: str) -> dict:
    response = _get_client().messages.create(
        model=MODEL,
        max_tokens=512,
        system=system,
        tools=[SYNTHESIS_TOOL],
        tool_choice={"type": "tool", "name": "judge_subtopic"},
        messages=[{"role": "user", "content": user}],
        extra_body={"temperature": 0},
    )
    tool_use = next((b for b in response.content if b.type == "tool_use"), None)
    if tool_use is None:
        return {"status": "established", "note": ""}
    return tool_use.input


if __name__ == "__main__":
    # CAPSTONE — pipeline REALE end-to-end (la lanci tu): decompose -> parallelo -> aggrega -> sintetizza.
    from sources import TOPIC
    from subagents import run_subagent, _call_haiku
    from coordinator import (decompose, run_all_parallel, aggregate, Assignment,
                             _call_coordinator_haiku)

    topic = TOPIC

    def run(a: Assignment) -> SubagentResult:
        return run_subagent(a.agent, a.channel, a.subtopic, topic, _call_haiku)

    assignments = decompose(topic, _call_coordinator_haiku)
    results = run_all_parallel(assignments, run)
    bundle = aggregate(results)
    report = synthesize(results, bundle.coverage_gaps, _call_synth_haiku)

    print("=== ESTABLISHED (ben supportato) ===")
    for f in report.established:
        print(f"  [{f.published_date}] {f.source_name}: {f.claim}")
    print("\n=== CONTESTED (conflitto preservato, non risolto) ===")
    for c in report.contested:
        print(f"  {c.topic} — {c.note}")
        for p in c.positions:
            print(f"     - [{p.published_date}] {p.source_name}: {p.claim}  ({p.source_ref})")
    print("\n=== COVERAGE GAPS ===")
    for g in report.coverage_gaps:
        print(f"  - {g}")