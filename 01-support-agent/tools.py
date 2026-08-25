"""Definizioni dei tool per l'API Anthropic, basate sulle funzioni in stubs.py."""

from stubs import get_employee, lookup_product_catalog, check_entitlement, provision_access

TOOLS = [
    {
        "name": "get_employee",
        "description": "Cerca un dipendente tramite la sua email aziendale.",
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
        "description": "Cerca un prodotto nel catalogo e ne restituisce costo per seat e disponibilità.",
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
        "description": "Verifica lo stato di assegnazione di un prodotto a un dipendente.",
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
