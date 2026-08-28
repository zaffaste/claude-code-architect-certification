"""Verifica deterministica del coordinator (nessuna API): coord finto + subagent finto,
piu' una prova REALE del parallelismo con uno sleep finto (thread, niente rete)."""
import time
from concurrent.futures import ThreadPoolExecutor  # noqa: F401 (usato indirettamente)
from models import FailureType, SubagentResult
from coordinator import (decompose, run_all_sequential, run_all_parallel, aggregate,
                         Assignment, AGENT_CHANNEL)

# --- coordinator finto: emette i 6 dispatch (ogni sottotema a entrambi i subagent) ---
def fake_coord(system, user):
    out = []
    for sub in ["productivity_metrics", "employee_wellbeing", "collaboration_costs"]:
        for agent in ["web_researcher", "doc_analyst"]:
            out.append({"agent": agent, "subtopic": sub})
    return out

# --- subagent finto (deterministico): la provenance NON viene da qui ---
def fake_subagent_call(system, user):
    return {"claim": "claim finto", "evidence_excerpt": "frammento finto"}

def run(a: Assignment) -> SubagentResult:
    from subagents import run_subagent
    return run_subagent(a.agent, a.channel, a.subtopic, "TOPIC", fake_subagent_call)

# 1) DECOMPOSE: 6 dispatch -> 6 assignment, canali mappati
assignments = decompose("TOPIC", fake_coord)
assert len(assignments) == 6, len(assignments)
assert all(a.channel == AGENT_CHANNEL[a.agent] for a in assignments)
print(f"OK decompose : {len(assignments)} assignment da 6 dispatch (menu vincolato, canali mappati)")

# 2) SEQ e PAR danno lo STESSO risultato (map preserva l'ordine)
seq = run_all_sequential(assignments, run)
par = run_all_parallel(assignments, run)
assert [r.model_dump() for r in seq] == [r.model_dump() for r in par]
print("OK seq==par  : parallelo e sequenziale producono risultati identici e ordinati")

# 3) AGGREGATE: 3 findings, 1 errore (timeout), 1 solo coverage gap = collaboration_costs
bundle = aggregate(par)
assert len(bundle.findings) == 3, len(bundle.findings)
assert len(bundle.errors) == 1 and bundle.errors[0].failure_type == FailureType.timeout
assert bundle.coverage_gaps == ["collaboration_costs: fonte non disponibile (timeout)"], bundle.coverage_gaps
print(f"OK aggregate : findings=3, errori=1(timeout), gap={bundle.coverage_gaps}")
print("             (productivity_metrics NON e' gap: 2 fonti; employee_wellbeing NON e' gap: doc copre; "
      "web/wellbeing vuoto-valido non conta come errore)")

# 4) PARALLELISMO reale (thread + sleep finto, niente rete): par deve battere seq
def slow_run(a):
    time.sleep(0.12)
    return SubagentResult(agent=a.agent, subtopic=a.subtopic)   # dummy

t0 = time.perf_counter(); run_all_sequential(assignments, slow_run); t_seq = time.perf_counter() - t0
t0 = time.perf_counter(); run_all_parallel(assignments, slow_run); t_par = time.perf_counter() - t0
assert t_par < t_seq * 0.5, (t_seq, t_par)
print(f"OK parallelo : seq={t_seq:.2f}s par={t_par:.2f}s -> par < seq/2 (i thread sovrappongono l'attesa)")

print("\nTUTTO VERDE - coordinator: decompose + parallelo + aggregate + coverage gap (nessuna API).")