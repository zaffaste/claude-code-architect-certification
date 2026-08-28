"""Il 'mondo' fixturato della research pipeline (Es. 4).
Determinismo sull'INPUT: le fonti sono fisse. Il non-determinismo resta dove serve
(le teste che ragionano: subagent e sintesi, chiamate vere). Qui vivono di proposito:
  - una COPPIA IN CONFLITTO su productivity_metrics (web +13% 2023  vs  doc -4% 2024),
  - un VUOTO VALIDO (nessuna fonte web su employee_wellbeing),
  - un TIMEOUT iniettato (web/collaboration_costs) -> fallimento d'accesso deterministico.

Dispatch previsto (lo usera' coordinator.py):
  productivity_metrics -> web + doc   (il conflitto emerge perche' due canali danno segni opposti)
  employee_wellbeing   -> web + doc   (web = vuoto valido; doc = finding)
  collaboration_costs  -> web         (web = timeout; nessuna fonte doc) -> COVERAGE GAP
"""
from dataclasses import dataclass
from datetime import date

TOPIC = "Impatto del lavoro da remoto sulla produttivita'"


@dataclass(frozen=True)
class Source:
    name: str
    ref: str            # URL (web) o nome documento (doc)
    published_date: date
    channel: str        # "web" | "doc"  -> quale subagent la raggiunge
    subtopic: str
    text: str           # cio' che il subagent 'legge' e struttura in un Finding


class SourceTimeout(Exception):
    """Fallimento d'accesso simulato, deterministico (niente sleep, niente API)."""


# (channel, subtopic) che scatena un timeout d'accesso.
TIMEOUT_COMBO = ("web", "collaboration_costs")

SOURCES: list[Source] = [
    # --- productivity_metrics: la coppia in conflitto (stesso tema, segni opposti, anni diversi) ---
    Source(
        name="GlobalWork Index 2023",
        ref="https://globalwork.example/index-2023",
        published_date=date(2023, 5, 10),
        channel="web",
        subtopic="productivity_metrics",
        text=("Il nostro sondaggio 2023 su 10.000 knowledge worker rileva che il lavoro da "
              "remoto ha aumentato la produttivita' auto-riportata del 13% rispetto all'ufficio."),
    ),
    Source(
        name="Acme Corp - Report interno Q4 2023",
        ref="Acme_Internal_Productivity_Q4-2023.pdf",
        published_date=date(2024, 2, 1),
        channel="doc",
        subtopic="productivity_metrics",
        text=("Misurando l'output effettivo (ticket chiusi, commit) dei team nel Q4 2023, il "
              "lavoro da remoto risulta associato a un calo del 4% della produttivita' rispetto "
              "al trimestre in ufficio."),
    ),
    # --- employee_wellbeing: solo doc. Sul canale web -> VUOTO VALIDO (cercato, nessun match) ---
    Source(
        name="WellbeingLab Whitepaper",
        ref="WellbeingLab_Remote_Burnout_2023.pdf",
        published_date=date(2023, 11, 20),
        channel="doc",
        subtopic="employee_wellbeing",
        text=("Su un campione di 4.200 dipendenti, chi lavora prevalentemente da remoto riporta "
              "un tasso di burnout inferiore del 22% rispetto ai colleghi in sede."),
    ),
    # --- collaboration_costs: nessuna fonte disponibile.
    #     web e' riggato a TIMEOUT; doc non ha fixture -> COVERAGE GAP nel report finale. ---
]


def retrieve(channel: str, subtopic: str) -> list[Source]:
    """Recupero deterministico. Distingue i tre esiti che la pipeline deve gestire:
      - lista non vuota  -> fonti trovate
      - lista vuota      -> vuoto valido (accesso ok, nessun match)
      - SourceTimeout    -> fallimento d'accesso (il subagent lo traduce in SubagentError)
    """
    if (channel, subtopic) == TIMEOUT_COMBO:
        raise SourceTimeout(f"Timeout su {channel}/{subtopic}")
    return [s for s in SOURCES if s.channel == channel and s.subtopic == subtopic]