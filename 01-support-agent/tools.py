"""Definizioni dei tool per l'API Anthropic, basate sulle funzioni in stubs.py."""

from stubs import (
    get_employee,
    lookup_product_catalog,
    check_entitlement,
    provision_access,
    escalate_to_human,
)

TOOLS = [
    {
        "name": "get_employee",
        "description": "Verifica l'identità dall'email e restituisce l'employee_id che gli altri tool richiedono.",
        "input_schema": {
            "type": "object",
            "properties": {
                "email": {
                    "type": "string",
                    "description": "Email del dipendente da cercare.",
                },
            },
            "required": ["email"],
        },
    },
    {
        "name": "lookup_product_catalog",
        "description": "Info di catalogo (costo/seat, disponibilità); usa per il prodotto in sé — prezzo, disponibilità. NON per cosa un dipendente possiede già → per quello usa check_entitlement",
        "input_schema": {
            "type": "object",
            "properties": {
                "product": {
                    "type": "string",
                    "description": "Nome del prodotto da cercare nel catalogo.",
                },
            },
            "required": ["product"],
        },
    },
    {
        "name": "check_entitlement",
        "description": "Cosa un dipendente specifico ha già assegnato; usa per il possesso/accesso di una persona. NON per prezzo o disponibilità → per quello usa lookup_product_catalog. Richiede un employee_id verificato da get_employee.",
        "input_schema": {
            "type": "object",
            "properties": {
                "employee_id": {
                    "type": "string",
                    "description": "ID del dipendente.",
                },
                "product": {
                    "type": "string",
                    "description": "Nome del prodotto.",
                },
            },
            "required": ["employee_id", "product"],
        },
    },
    {
        "name": "provision_access",
        "description": "Assegna l'accesso a un prodotto per un dipendente.",
        "input_schema": {
            "type": "object",
            "properties": {
                "employee_id": {
                    "type": "string",
                    "description": "ID del dipendente.",
                },
                "product": {
                    "type": "string",
                    "description": "Nome del prodotto da assegnare.",
                },
                "quantity": {
                    "type": "integer",
                    "description": "Numero di seat da assegnare. Default 1.",
                },
            },
            "required": ["employee_id", "product"],
        },
    },
    {
        "name": "escalate_to_human",
        "description": (
            "Inoltra la richiesta a un operatore umano quando non può essere gestita "
            "automaticamente. Usa quando: l'utente chiede esplicitamente un umano; la "
            "richiesta è fuori dallo scope dei tool disponibili (es. rete, VPN, hardware); "
            "un'operazione è bloccata e richiede approvazione. Fornisci un summary utile "
            "all'operatore."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "reason": {
                    "type": "string",
                    "enum": ["spend_over_limit", "out_of_scope",
                             "explicit_human_request", "no_progress"],
                    "description": "Categoria del motivo di escalation.",
                },
                "summary": {
                    "type": "string",
                    "description": "Riassunto per l'operatore: cosa ha chiesto l'utente e cosa blocca l'automazione.",
                },
                "employee_id": {
                    "type": "string",
                    "description": "ID del dipendente coinvolto, se noto.",
                },
                "product": {
                    "type": "string",
                    "description": "Prodotto coinvolto, se noto.",
                },
            },
            "required": ["reason", "summary"],
        },
    },
]

TOOL_FUNCTIONS = {
    "get_employee": get_employee,
    "lookup_product_catalog": lookup_product_catalog,
    "check_entitlement": check_entitlement,
    "provision_access": provision_access,
    "escalate_to_human": escalate_to_human,
}
