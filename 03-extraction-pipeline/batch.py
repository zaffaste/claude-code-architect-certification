import time
from extraction_retry import client, MODEL, SYSTEM_NULL_RULE, extraction_tool
from dataclasses import dataclass, field
from models import Ticket
from validation import Issue, check
from pipeline import _assemble
import time


@dataclass
class Buckets:
    valid: list = field(default_factory=list)     # Ticket completi
    routed: list = field(default_factory=list)    # (tid, Ticket|None, issues) -> umano
    rebatch: list = field(default_factory=list)   # (tid, issues) -> secondo batch (validazione retryable)
    resubmit: list = field(default_factory=list)  # tid -> errore batch-level, risottometti


def build_batch_requests(tickets):
    """Un forced-extraction ONE-SHOT per ticket. Niente loop: il retry non può stare qui."""
    return [
        {
            "custom_id": tid,   # correla risultato->ticket; l'ordine NON è garantito
            "params": {
                "model": MODEL,
                "max_tokens": 1024,
                "system": SYSTEM_NULL_RULE,
                "tools": [extraction_tool],
                "tool_choice": {"type": "tool", "name": extraction_tool["name"]},
                "messages": [{"role": "user", "content": raw}],
            },
        }
        for tid, raw in tickets
    ]


# def submit_and_wait(tickets, poll_seconds=30):
#     """Sottomette il batch e attende la fine. Ritorna la lista dei risultati (custom_id, result)."""
#     batch = client.messages.batches.create(requests=build_batch_requests(tickets))
#     while True:
#         status = client.messages.batches.retrieve(batch.id)
#         if status.processing_status == "ended":
#             break
#         time.sleep(poll_seconds)
#     return list(client.messages.batches.results(batch.id))

def submit_and_wait(tickets, poll_seconds=10):
    batch = client.messages.batches.create(requests=build_batch_requests(tickets))
    print(f"batch {batch.id} sottomesso; attendo (nessun SLA garantito)...")
    start = time.time()
    while True:
        status = client.messages.batches.retrieve(batch.id)
        c = status.request_counts
        print(f"  [{int(time.time() - start)}s] stato={status.processing_status} "
              f"processing={c.processing} ok={c.succeeded} errori={c.errored}")
        if status.processing_status == "ended":
            break
        time.sleep(poll_seconds)
    return list(client.messages.batches.results(batch.id))

def max_submission_interval_hours(sla_hours, batch_window_hours=24):
    """Peggior caso end-to-end = intervallo_tra_sottomissioni + finestra_batch.
    Per garantire l'SLA:  intervallo <= SLA - finestra."""
    return sla_hours - batch_window_hours

def normalize_result(entry):
    """Adatta un risultato SDK -> (custom_id, status, data). Unico punto che tocca l'SDK."""
    if entry.result.type != "succeeded":
        return (entry.custom_id, "errored", None)          # errored/canceled/expired
    block = next((b for b in entry.result.message.content if b.type == "tool_use"), None)
    return (entry.custom_id, "succeeded", block.input) if block else (entry.custom_id, "errored", None)


def process_results(normalized, tickets_by_id):
    """Logica pura: smista i risultati normalizzati nei quattro bucket."""
    b = Buckets()
    for custom_id, status, data in normalized:
        if status == "errored" or data is None:
            b.resubmit.append(custom_id)
            continue
        result, issues = check(data)
        raw = tickets_by_id[custom_id]
        if not issues:
            b.valid.append(_assemble(result, custom_id, raw))
        elif any(not i.retryable for i in issues):
            b.routed.append((custom_id, _assemble(result, custom_id, raw), issues))
        else:
            b.rebatch.append((custom_id, issues))
    return b


def _submit_real(pending):
    """submit di produzione: sottomette, attende, normalizza."""
    return [normalize_result(e) for e in submit_and_wait(pending)]


def run_batch_pipeline(tickets, submit=_submit_real, max_rounds=2):
    """tickets: lista di (ticket_id, raw). 'submit' è iniettato -> testabile con un simulatore."""
    tickets_by_id = dict(tickets)
    pending = list(tickets)
    valid, routed = [], []
    for round_no in range(max_rounds + 1):
        b = process_results(submit(pending), tickets_by_id)
        valid.extend(b.valid)
        routed.extend(b.routed)
        retry = b.rebatch + [(tid, None) for tid in b.resubmit]
        if not retry or round_no == max_rounds:
            for tid, issues in retry:                       # residuo irrisolto dopo l'ultimo round -> umano
                routed.append((tid, None, issues or [Issue(tid, "non risolto dopo i round di batch", False)]))
            return valid, routed, round_no + 1
        # prossimo giro: rebatch con feedback NEL TESTO (opzione a), resubmit as-is
        pending = []
        for tid, issues in b.rebatch:
            err = "; ".join(f"{i.field}: {i.message}" for i in issues)
            pending.append((tid, f"[Estrazione precedente non valida: {err}. Correggi.]\n{tickets_by_id[tid]}"))
        for tid in b.resubmit:
            pending.append((tid, tickets_by_id[tid]))       # se l'errore fosse 'oversize', qui spezzeresti il documento
    return valid, routed, max_rounds + 1

if __name__ == "__main__":
    tickets = [
        ("SD-3001", "Da g.bianchi@reti.it: servono 2 licenze Visio."),
        ("SD-3002", "Ciao, 3 Copilot per marketing. Anna"),          # -> routed, nessun identificativo
    ]
    valid, routed, rounds = run_batch_pipeline(tickets)
    print(f"round: {rounds}")
    for t in valid:
        print(f"VALID  {t.ticket_id}")
    for tid, _tk, issues in routed:
        print(f"ROUTED {tid}: " + "; ".join(i.field for i in issues))