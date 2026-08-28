"""Verifica deterministica della sintesi (nessuna API): fake ovunque.
Prova la proprieta' che conta: ENTRAMBI i valori in conflitto sopravvivono con attribuzione,
la nota temporale c'e', established non spende chiamate, e il tool non espone le fonti."""
from models import FailureType
from coordinator import decompose, run_all_sequential, aggregate, Assignment
from subagents import run_subagent
from synthesis import synthesize, SYNTHESIS_TOOL

# --- ricostruisco results in modo deterministico riusando la catena del coordinator ---
def fake_coord(system, user):
    out = []
    for sub in ["productivity_metrics", "employee_wellbeing", "collaboration_costs"]:
        for agent in ["web_researcher", "doc_analyst"]:
            out.append({"agent": agent, "subtopic": sub})
    return out

def fake_subagent_call(system, user):
    # claim diverso per fonte, cosi' vediamo che ENTRAMBI restano distinti
    return {"claim": user.split("\n")[-1][:40], "evidence_excerpt": "frammento finto"}

def run(a: Assignment):
    return run_subagent(a.agent, a.channel, a.subtopic, "TOPIC", fake_subagent_call)

assignments = decompose("TOPIC", fake_coord)
results = run_all_sequential(assignments, run)
gaps = aggregate(results).coverage_gaps

# --- sintesi con call finta che conta le invocazioni ---
CALLS = {"n": 0}
def fake_synth_call(system, user):
    CALLS["n"] += 1
    return {"status": "contested", "note": "valori opposti; date diverse (2023 vs 2024): possibile differenza temporale"}

report = synthesize(results, gaps, fake_synth_call)

# 1) SOLO il sottotema con >=2 findings spende una chiamata (productivity_metrics)
assert CALLS["n"] == 1, CALLS["n"]
print(f"OK 1 chiamata: solo il sottotema conteso (>=2 findings) ha speso una call ({CALLS['n']})")

# 2) established: employee_wellbeing (1 finding) senza chiamata
assert len(report.established) == 1
print(f"OK established: {len(report.established)} finding (employee_wellbeing), nessuna chiamata")

# 3) contested: ENTRAMBI i valori preservati, con provenance e date distinte
assert len(report.contested) == 1
c = report.contested[0]
assert c.topic == "productivity_metrics"
assert len(c.positions) == 2
names = {p.source_name for p in c.positions}
years = sorted({p.published_date.year for p in c.positions})
assert names == {"GlobalWork Index 2023", "Acme Corp - Report interno Q4 2023"}, names
assert years == [2023, 2024], years
assert c.note and "temporale" in c.note.lower()
print(f"OK contested : 2 posizioni preservate, fonti {sorted(names)}, anni {years}, nota temporale presente")

# 4) il modello NON puo' scegliere: il tool espone solo status+note
props = set(SYNTHESIS_TOOL["input_schema"]["properties"])
assert props == {"status", "note"}, props
print("OK tool schema: espone solo status+note; le fonti sono fuori dalla portata del modello")

# 5) coverage gap propagato
assert report.coverage_gaps == ["collaboration_costs: fonte non disponibile (timeout)"], report.coverage_gaps
print(f"OK gap        : {report.coverage_gaps}")

print("\nTUTTO VERDE - synthesis: conflitto preservato (non risolto), provenance intatta, 1 sola call.")