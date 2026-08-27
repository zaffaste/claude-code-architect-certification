from dataclasses import dataclass
from pydantic import ValidationError
from models import ExtractionResult, RequestType

ESCAPE_TYPES = (RequestType.other, RequestType.unclear)


@dataclass
class Issue:
    field: str
    message: str      # specifico: verrà rimandato al modello sul retry
    retryable: bool


def normalize(result: ExtractionResult) -> ExtractionResult:
    """Correzioni deterministiche: ciò che non va dedotto si sistema in codice."""
    if result.request_type not in ESCAPE_TYPES and result.request_type_detail is not None:
        result.request_type_detail = None
    return result


def check(data: dict) -> tuple[ExtractionResult | None, list[Issue]]:
    # 1. SCHEMA -> errori di forma, RETRYABLE
    try:
        result = ExtractionResult.model_validate(data)
    except ValidationError as e:
        issues = [Issue(".".join(str(x) for x in err["loc"]), err["msg"], retryable=True)
                  for err in e.errors()]
        return None, issues

    result = normalize(result)
    issues: list[Issue] = []

    # 2. detail obbligatorio se type è other/unclear -> CONTENUTO assente, non retryable
    if result.request_type in ESCAPE_TYPES and result.request_type_detail is None:
        issues.append(Issue("request_type_detail",
            "request_type è 'other'/'unclear' ma manca il dettaglio.", retryable=False))

    # 3. identità richiedente assente -> CONTENUTO assente, non retryable
    if result.requester.employee_id is None and result.requester.email is None:
        issues.append(Issue("requester",
            "Nessun identificativo (employee_id/email): identità non verificabile.", retryable=False))

    # 4. totale dichiarato vs somma righe -> CONFLITTO sorgente, non retryable
    if (result.stated_total_eur is not None and result.items
            and all(i.quantity is not None and i.unit_cost_eur is not None for i in result.items)):
        calc = sum(i.quantity * i.unit_cost_eur for i in result.items)
        if abs(calc - result.stated_total_eur) > 0.01:
            issues.append(Issue("stated_total_eur",
                f"Totale dichiarato {result.stated_total_eur} != somma righe {calc}.", retryable=False))

    return result, issues