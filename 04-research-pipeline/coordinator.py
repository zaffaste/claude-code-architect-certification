"""Coordinator della research pipeline (Es. 4) — hub-and-spoke.

Responsabilita' (tutte qui, tranne la sintesi che e' il prossimo componente):
1. DECOMPONE (chiamata Haiku vera, menu vincolato): emette PIU' dispatch_subagent in UN turno
   (Card 2 / Task 1.3). L'enum sui sottotemi impedisce assegnazioni fuori-fixture.
2. DISPATCH parallelo vs sequenziale (codice): i subagent sono I/O-bound (HTTP) -> ThreadPool
   li sovrappone davvero; misuriamo il delta di latenza (Es. 4 step 2).
3. AGGREGA (codice): raccoglie i SubagentResult, separa errori, calcola i COVERAGE GAP
   (sottotemi finiti a zero findings) -> un timeout non blocca, diventa lacuna annotata (Task 5.3).

Substrato B: il turno del coordinator produce SOLO il piano; non rimandiamo tool_result al
coordinator (nessun secondo giro). L'esecuzione e l'aggregazione sono deterministiche in codice.
"""
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor
from time import perf_counter

from sources import TOPIC
from models import Finding, SubagentResult, SubagentError
from subagents import MODEL, run_subagent, _call_haiku, _get_client

# --- Menu VINCOLATO: agenti, canali, sottotemi ammessi (l'enum li impone al modello) ---
AGENT_CHANNEL = {"web_researcher": "web", "doc_analyst": "doc"}
SUBTOPICS = ["productivity_metrics", "employee_wellbeing", "collaboration_costs"]

DISPATCH_TOOL = {
    "name": "dispatch_subagent",
    "description": ("Assegna UN sottotema a UN subagent. Emetti una chiamata di questo tool per "
                    "OGNI coppia (subagent, sottotema), tutte nello stesso turno."),
    "input_schema": {
        "type": "object",
        "properties": {
            "agent": {"type": "string", "enum": list(AGENT_CHANNEL)},
            "subtopic": {"type": "string", "enum": SUBTOPICS},
        },
        "required": ["agent", "subtopic"],
    },
}

COORD_SYSTEM = (
    "Sei il coordinator di una pipeline di ricerca multi-agente. Due subagent:\n"
    "- web_researcher (fonti web)\n"
    "- doc_analyst (documenti/report)\n\n"
    "Assegna il lavoro chiamando dispatch_subagent UNA VOLTA per ogni coppia (subagent, sottotema), "
    "EMETTENDO TUTTE le chiamate NELLO STESSO TURNO.\n"
    "Sottotemi da coprire: productivity_metrics, employee_wellbeing, collaboration_costs.\n"
    "Assegna OGNI sottotema a ENTRAMBI i subagent, cosi' da triangolare le fonti e far emergere "
    "eventuali valori in conflitto."
    # NB tradeoff d'esame: 'ogni sottotema a entrambi' massimizza la COPERTURA (e fa emergere i
    # conflitti), ma DUPLICA. In un sistema a costo reale partizioneresti per non duplicare
    # (Task 1.2). Qui la duplicazione e' voluta: serve a far vedere conflitto + vuoto-valido + timeout.
)


@dataclass(frozen=True)
class Assignment:
    agent: str
    channel: str
    subtopic: str


def decompose(topic: str, call_coord) -> list[Assignment]:
    """call_coord(system, user) -> list[dict], gli input dei dispatch emessi in UN turno.
    Traduce i dispatch in Assignment, con dedup difensivo (il modello potrebbe ripetere una coppia)."""
    dispatches = call_coord(COORD_SYSTEM, f"TOPIC: {topic}")
    seen: set[tuple[str, str]] = set()
    assignments: list[Assignment] = []
    for d in dispatches:
        key = (d["agent"], d["subtopic"])
        if key in seen:
            continue
        seen.add(key)
        assignments.append(Assignment(d["agent"], AGENT_CHANNEL[d["agent"]], d["subtopic"]))
    return assignments


def run_all_sequential(assignments: list[Assignment], run) -> list[SubagentResult]:
    """Baseline: un subagent alla volta."""
    return [run(a) for a in assignments]


def run_all_parallel(assignments: list[Assignment], run) -> list[SubagentResult]:
    """Parallelo: i subagent sono I/O-bound -> i thread ne sovrappongono l'attesa di rete.
    map() preserva l'ordine -> aggregazione deterministica."""
    if not assignments:
        return []
    with ThreadPoolExecutor(max_workers=len(assignments)) as ex:
        return list(ex.map(run, assignments))


@dataclass
class ResearchBundle:
    findings: list[Finding] = field(default_factory=list)
    errors: list[SubagentError] = field(default_factory=list)
    coverage_gaps: list[str] = field(default_factory=list)


def aggregate(results: list[SubagentResult]) -> ResearchBundle:
    """Hub: raccoglie tutto. Un sottotema con ZERO findings totali e' un COVERAGE GAP,
    annotato col motivo (timeout vs nessuna fonte). L'errore non blocca il resto."""
    findings = [f for r in results for f in r.findings]
    errors = [r.error for r in results if r.error is not None]

    by_subtopic: dict[str, list[SubagentResult]] = {}
    for r in results:
        by_subtopic.setdefault(r.subtopic, []).append(r)

    gaps: list[str] = []
    for subtopic, rs in by_subtopic.items():
        if sum(len(r.findings) for r in rs) == 0:                 # nessuno ha trovato nulla
            had_error = any(r.error is not None for r in rs)
            reason = "fonte non disponibile (timeout)" if had_error else "nessuna fonte trovata"
            gaps.append(f"{subtopic}: {reason}")

    return ResearchBundle(findings=findings, errors=errors, coverage_gaps=sorted(gaps))


# --- Chiamata reale del coordinator: la lanci TU. Restituisce i dispatch emessi nel turno. ---
def _call_coordinator_haiku(system: str, user: str) -> list[dict]:
    response = _get_client().messages.create(
        model=MODEL,
        max_tokens=512,
        system=system,
        tools=[DISPATCH_TOOL],
        tool_choice={"type": "any"},          # deve chiamare un tool; PUO' emetterne piu' in un turno
        messages=[{"role": "user", "content": user}],
        extra_body={"temperature": 0},
    )
    return [b.input for b in response.content if b.type == "tool_use"]


if __name__ == "__main__":
    # CHIAMATA REALE (la lanci tu): decompone -> misura seq vs par -> aggrega.
    topic = TOPIC

    def run(a: Assignment) -> SubagentResult:
        return run_subagent(a.agent, a.channel, a.subtopic, topic, _call_haiku)

    assignments = decompose(topic, _call_coordinator_haiku)
    print(f"DISPATCH emessi in un turno: {len(assignments)}")
    for a in assignments:
        print(f"  - {a.agent:14s} <- {a.subtopic}  (canale {a.channel})")

    t0 = perf_counter(); seq = run_all_sequential(assignments, run); t_seq = perf_counter() - t0
    t0 = perf_counter(); par = run_all_parallel(assignments, run);   t_par = perf_counter() - t0
    speedup = t_seq / t_par if t_par else float("inf")
    print(f"\nlatenza sequenziale: {t_seq:.2f}s | parallela: {t_par:.2f}s | speedup x{speedup:.1f}")

    bundle = aggregate(par)
    print(f"\nfindings: {len(bundle.findings)} | errori: {len(bundle.errors)} | "
          f"coverage gap: {bundle.coverage_gaps}")
    for f in bundle.findings:
        print(f"  [{f.published_date}] {f.source_name}: {f.claim}")