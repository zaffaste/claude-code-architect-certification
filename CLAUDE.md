# CCARF Exercises — Project Rules

Progetto di studio per la certificazione CCAR-F. Esercizi di architettura
agentica in Python, costruiti passo per passo. Priorità: chiarezza e
capacità di ragionare sul codice, non completezza o robustezza da produzione.

## Codice
- Scrivi solo il codice Python necessario a soddisfare la richiesta. Niente
  funzionalità non richieste, niente astrazioni premature.
- Il codice deve spiegarsi da solo: nomi chiari, funzioni piccole e a
  responsabilità singola.
- Aggiungi commenti dove chiariscono il *perché* di una scelta, non dove
  ripetono ciò che il codice già dice.
- Preferisci soluzioni semplici e leggibili a soluzioni "furbe".

## Vincoli didattici
- Non aggiungere gestione errori, async, logging o dipendenze se non sono
  esplicitamente richiesti nel passo corrente.
- Gli stub e i dati di test sono deterministici: stesso input, stesso output.
  Nessuna casualità, nessuna chiamata di rete o a database.
- Quando una decisione ha alternative valide, fermati e chiedi invece di
  sceglierla in autonomia.

## Flusso di lavoro
- Un passo alla volta. Non anticipare passi successivi né creare file non
  richiesti.
- Non modificare file esistenti senza che sia chiesto.

## Test
- I test vivono accanto al modulo che verificano e ne asseriscono il
  comportamento; non stampano, verificano.
- Un test è deterministico e isolato: nessuna chiamata reale all'API o alla
  rete, si appoggia agli stub.