"""Verifica deterministica (nessuna API): i modelli si costruiscono e retrieve() da' i tre esiti."""
from datetime import date
from models import Finding, SynthesisReport
from sources import retrieve, SourceTimeout, TIMEOUT_COMBO

# 1) i modelli si costruiscono e validano (con coercizione str->date, come fara' il tool_use vero)
f = Finding(claim="+13% produttivita'", evidence_excerpt="...del 13%...",
            source_name="GlobalWork Index 2023", source_ref="https://globalwork.example/index-2023",
            published_date="2023-05-10")
rep = SynthesisReport(established=[f], coverage_gaps=["collaboration_costs"])
assert rep.established[0].published_date == date(2023, 5, 10)
print("OK modelli   : Finding + SynthesisReport costruiti; str->date coerced")

# 2) retrieve(): TROVATO
got = retrieve("web", "productivity_metrics")
assert len(got) == 1 and got[0].name == "GlobalWork Index 2023"
print(f"OK trovato   : web/productivity_metrics -> {len(got)} fonte")

# 3) retrieve(): VUOTO VALIDO (accesso ok, nessun match) -- NON un errore
assert retrieve("web", "employee_wellbeing") == []
print("OK vuoto-val.: web/employee_wellbeing  -> [] (accesso ok, nessun match)")

# 4) retrieve(): TIMEOUT = fallimento d'accesso, distinto dal vuoto valido
try:
    retrieve(*TIMEOUT_COMBO)
    raise AssertionError("doveva sollevare SourceTimeout")
except SourceTimeout as e:
    print(f"OK timeout   : {TIMEOUT_COMBO[0]}/{TIMEOUT_COMBO[1]} -> SourceTimeout ({e})")

# 5) il conflitto e' presente nel corpus: stesso subtopic, due canali, due anni
prod = [s for s in __import__('sources').SOURCES if s.subtopic == "productivity_metrics"]
anni = sorted(s.published_date.year for s in prod)
assert len(prod) == 2 and anni == [2023, 2024]
print(f"OK conflitto : productivity_metrics -> 2 fonti, anni {anni} (segni opposti, temporalmente distinte)")

print("\nTUTTO VERDE - mondo fixturato e contratto dati pronti.")