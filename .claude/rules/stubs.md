---
paths: ["**/stubs.py"]
---
# Regole per gli stub
- Gli stub sono dati finti deterministici: stesso input, stesso output.
- Nessuna logica reale: niente try/except, logging, I/O, DB o rete.
- Niente print o blocchi di prova nel modulo; le verifiche stanno fuori.