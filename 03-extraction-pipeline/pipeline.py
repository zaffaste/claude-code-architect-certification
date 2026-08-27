from dataclasses import dataclass
from models import Ticket
from validation import Issue, check


@dataclass
class Outcome:
    status: str                     # "valid" | "routed" | "no_extraction"
    ticket: Ticket | None           # popolato anche in "routed" se lo schema è passato (handoff a umano)
    issues: list[Issue]
    attempts: int


def _assemble(result, ticket_id, raw_text):
    return Ticket(ticket_id=ticket_id, raw_text=raw_text, **result.model_dump()) if result else None


def run_extraction(raw_text, ticket_id, call, tool_name, max_retries=2):
    """Loop deterministico attorno a check(). 'call' è iniettato -> testabile senza API."""
    messages = [{"role": "user", "content": raw_text}]
    for attempt in range(max_retries + 1):
        got = call(messages)
        if got is None:                                   # niente tool_use (refusal/max_tokens)
            return Outcome("no_extraction", None, [], attempt + 1)
        tool_use_id, data = got
        result, issues = check(data)

        if not issues:                                    # VALIDO
            return Outcome("valid", _assemble(result, ticket_id, raw_text), [], attempt + 1)

        if any(not i.retryable for i in issues):          # contenuto/conflitto -> ROUTE, niente retry
            return Outcome("routed", _assemble(result, ticket_id, raw_text), issues, attempt + 1)

        if attempt == max_retries:                        # tutti retryable ma budget finito (rete di sicurezza)
            return Outcome("routed", _assemble(result, ticket_id, raw_text), issues, attempt + 1)

        # tutti retryable e c'è budget -> feedback via tool_result e ritenta
        errors = "; ".join(f"{i.field}: {i.message}" for i in issues)
        messages.append({"role": "assistant", "content": [
            {"type": "tool_use", "id": tool_use_id, "name": tool_name, "input": data}]})
        messages.append({"role": "user", "content": [
            {"type": "tool_result", "tool_use_id": tool_use_id,
             "content": f"Validazione fallita: {errors}", "is_error": True},
            {"type": "text", "text": "Ripeti l'estrazione correggendo esattamente questi punti."}]})