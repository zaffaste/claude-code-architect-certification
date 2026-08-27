from extraction_retry import call_model, SYSTEM_NULL_RULE, SYSTEM_FEWSHOT

tricky = {
    "idioma 'un paio'": "Per il team acquisti serve un paio di licenze Visio. p.neri@reti.it",
    "budget/no-unit":   "Servono 4 licenze Project, budget 400 EUR totali. s.gallo@reti.it",
    "formato tabella":  "Richiedente | Prodotto | Qtà\nc.ricci@reti.it | Power BI Pro | 6",
}

def fields(data):
    items = data.get("items") or [{}]
    return [(i.get("product"), i.get("quantity"), i.get("unit_cost_eur")) for i in items], data.get("stated_total_eur")

for nome, raw in tricky.items():
    print(f"\n### {nome}\n{raw!r}")
    for etichetta, sysp in [("SENZA few-shot", SYSTEM_NULL_RULE), ("CON few-shot ", SYSTEM_FEWSHOT)]:
        res = call_model([{"role": "user", "content": raw}], system=sysp)
        if res is None:
            print(f"  {etichetta}: no tool_use")
            continue
        items, total = fields(res[1])
        print(f"  {etichetta}: items(prod,qty,unit)={items}  total={total}")