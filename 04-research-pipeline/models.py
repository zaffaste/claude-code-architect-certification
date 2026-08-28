"""Modelli Pydantic della research pipeline (Es. 4) — il contratto dati dell'intero esercizio.
Ogni modello mappa un requisito d'esame:
- Finding        : claim-source mapping con data (Task 1.3 / 5.6) = provenance che la sintesi deve preservare.
- SubagentError  : contesto d'errore STRUTTURATO (Task 5.3), non un "search unavailable" generico.
- SubagentResult : distingue 'trovato' / 'vuoto valido' / 'errore' (Card 5 riusata in D5).
- SynthesisReport: established vs contested vs coverage_gaps (Task 5.6) — i conflitti si preservano, non si risolvono a caso.
"""
from datetime import date
from enum import Enum
from pydantic import BaseModel, Field


class Finding(BaseModel):
    claim: str
    evidence_excerpt: str
    source_name: str
    source_ref: str            # URL (web) o nome documento (doc)
    published_date: date       # la data separa 'conflitto reale' da 'differenza temporale' (Task 5.6)


class FailureType(str, Enum):
    timeout = "timeout"
    source_unavailable = "source_unavailable"


class SubagentError(BaseModel):
    failure_type: FailureType
    attempted_query: str                                   # cosa cercava: abilita retry/alternativa nel coordinator
    partial_results: list[Finding] = Field(default_factory=list)
    detail: str


class SubagentResult(BaseModel):
    """Esito di un subagent. TRE stati distinti, non due:
      - findings non vuoto          -> trovato
      - findings vuoto, error None  -> VUOTO VALIDO (accesso ok, nessun match)
      - error valorizzato           -> FALLIMENTO d'accesso (decisione di recovery al coordinator)
    Collassare vuoto-valido e fallimento e' l'anti-pattern (Card 5 / Task 5.3)."""
    agent: str
    subtopic: str
    findings: list[Finding] = Field(default_factory=list)
    error: SubagentError | None = None


class ContestedClaim(BaseModel):
    topic: str
    positions: list[Finding]             # entrambi i valori, ciascuno con la sua fonte+data
    note: str | None = None              # es. "possibile differenza temporale, non contraddizione"


class SynthesisReport(BaseModel):
    established: list[Finding] = Field(default_factory=list)       # ben supportato
    contested: list[ContestedClaim] = Field(default_factory=list)  # conflitti preservati con attribuzione
    coverage_gaps: list[str] = Field(default_factory=list)         # sottotemi non coperti (fonte non disponibile)