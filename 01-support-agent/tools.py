"""Definizioni dei tool per l'API Anthropic, basate sulle funzioni in stubs.py."""

from stubs import get_employee, lookup_product_catalog, check_entitlement, provision_access

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
            },
            "required": ["employee_id", "product"],
        },
    },
]

TOOL_FUNCTIONS = {
    "get_employee": get_employee,
    "lookup_product_catalog": lookup_product_catalog,
    "check_entitlement": check_entitlement,
    "provision_access": provision_access,
}
