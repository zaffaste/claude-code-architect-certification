from mcp.server.mcpserver import MCPServer

mcp = MCPServer("ccarf-quiz")

@mcp.tool()
def domain_weight(domain: str) -> dict:
    """Restituisce il peso percentuale di un dominio d'esame CCAR-F.
    Argomento: domain (es. 'D1', 'D2'). Ritorna un dict con dominio e peso."""
    pesi = {"D1": 27, "D2": 18, "D3":20, "D4": 20, "D5": 15}
    return {"domain": domain, "weight_percent": pesi.get(domain, 0)}

if __name__ == "__main__":
    mcp.run()