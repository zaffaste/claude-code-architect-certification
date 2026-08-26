---
name: scenario-quiz
description: Genera 3 domande scenario in stile esame CCAR-F dal file indicato.
argument-hint: "[percorso-file]"
context: fork
allowed-tools: Read
disable-model-invocation: true
---

Leggi il file al percorso `$ARGUMENTS` e genera **esattamente 3 domande
scenario** in stile CCAR-F sui pattern presenti nel file.

Per ogni domanda:
- descrivi una situazione di produzione realistica (1-2 frasi);
- proponi 4 opzioni plausibili, di cui una sola corretta;
- indica la corretta e, in una riga, perché ciascun distrattore è sbagliato;
- chiudi con il principio architetturale che la domanda verifica.

Concentrati sul quando/perché/tradeoff, non sulla sintassi. Non modificare file.