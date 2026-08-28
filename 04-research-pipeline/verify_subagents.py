"""Verifica deterministica del subagent (nessuna API): call finta iniettata.
Prova i tre esiti + la ownership della provenance, e che vuoto/timeout NON spendono chiamate."""
from datetime import date
from models import FailureType
from subagents import run_subagent, FINDING_TOOL

CALLS = {"n": 0}
def fake_call(system, user):
    CALLS["n"] += 1                     # contiamo le chiamate: vuoto/timeout non devono spenderne
    return {"claim": "claim finto", "evidence_excerpt": "frammento finto"}

# 1) TROVATO: web/productivity_metrics -> 1 fonte -> 1 finding con provenance dal FIXTURE
r = run_subagent("web_researcher", "web", "productivity_metrics", "TOPIC", fake_call)
assert r.error is None and len(r.findings) == 1
f = r.findings[0]
assert f.claim == "claim finto"                              # parte cognitiva: dal modello
assert f.source_name == "GlobalWork Index 2023"              # provenance: dal fixture, non dal modello
assert f.source_ref == "https://globalwork.example/index-2023"
assert f.published_date == date(2023, 5, 10)
print("OK trovato   : 1 finding; claim dal modello, provenance AUTOREVOLE dal fixture")

# 2) VUOTO VALIDO: web/employee_wellbeing -> 0 fonti -> nessun errore e ZERO chiamate
before = CALLS["n"]
r = run_subagent("web_researcher", "web", "employee_wellbeing", "TOPIC", fake_call)
assert r.error is None and r.findings == [] and CALLS["n"] == before
print("OK vuoto-val.: findings=[] senza errore, ZERO call spese")

# 3) TIMEOUT: errore strutturato, ZERO chiamate
before = CALLS["n"]
r = run_subagent("web_researcher", "web", "collaboration_costs", "TOPIC", fake_call)
assert r.findings == [] and r.error is not None
assert r.error.failure_type == FailureType.timeout and CALLS["n"] == before
print(f"OK timeout   : SubagentError(failure_type={r.error.failure_type.value}), "
      f"ZERO call, attempted_query='{r.error.attempted_query}'")

# 4) il TOOL non espone la provenance -> il modello non puo' fabbricarla
props = set(FINDING_TOOL["input_schema"]["properties"])
assert props == {"claim", "evidence_excerpt"}, props
print("OK tool schema: espone solo claim+evidence; provenance fuori dalla portata del modello")

print(f"\nTUTTO VERDE - subagent ok. Chiamate cognitive totali spese nel test: {CALLS['n']} (solo sul caso 'trovato').")