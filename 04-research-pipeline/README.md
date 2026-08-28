# Esercizio 4 — Multi-Agent Research Pipeline (CCAR-F)

Pipeline di ricerca multi-agente costruita per allenare il **giudizio architetturale** dei
domini **D1** (Agentic Architecture & Orchestration), **D2** (Tool Design & MCP Integration),
**D5** (Context Management & Reliability). Non e' codice fine a se': ogni scelta mappa un task
statement e una decisione con tradeoff.

## Substrato: orchestrazione a mano su Messages API grezza (non Agent SDK)

L'esame veste gli scenari col vocabolario dell'Agent SDK (`AgentDefinition`, Task/Agent tool,
`allowedTools`). Qui pero' l'orchestrazione e' **implementata a mano** sulla Messages API, perche'
gli step dell'esercizio richiedono di *iniettare e misurare* cose che l'SDK non lascia controllare:
un timeout a comando, due fonti in conflitto deterministiche, il delta di latenza parallelo/sequenziale.
La superficie SDK e' comunque toccata a parte in `spike_agent_sdk.py`.

Principio guida: **mondo = stub deterministico / teste = chiamate vere**. L'input (le fonti) e'
fisso; il non-determinismo resta solo dove serve osservarlo (i modelli che ragionano). Le chiamate
reali sono su `claude-haiku-4-5-20251001`, temperatura 0.

## I moduli

| File | Cosa fa |
|------|---------|
| `sources.py` | Il "mondo" fixturato: corpus, una coppia in conflitto, un vuoto-valido, un timeout iniettato. `retrieve()` ha tre esiti. |
| `models.py` | Contratto dati Pydantic: `Finding`, `SubagentError`, `SubagentResult`, `ContestedClaim`, `SynthesisReport`. |
| `subagents.py` | Il subagent: contesto **esplicito** nel prompt, chiamata Haiku vera, provenance **code-owned**. |
| `coordinator.py` | Decompone (menu vincolato), dispaccia **parallelo vs sequenziale**, aggrega, calcola i **coverage gap**. |
| `synthesis.py` | Preserva il conflitto (non lo risolve), annota la differenza temporale, struttura established/contested/gap. E' anche il **capstone** end-to-end. |
| `spike_agent_sdk.py` | Evidenza a parte: coordinator->subagent col **vero** `claude-agent-sdk`. |
| `verify_*.py` | Quattro verifier **deterministici** (nessuna API): logica provata con call finte iniettate. |

## Mappa: step della guida -> file/funzione -> dominio

| Step Es. 4 | Dove | Dominio / Task |
|------------|------|----------------|
| Coordinator + subagent, contesto esplicito (non ereditato) | `coordinator.decompose` + `subagents.build_prompt` | D1 / 1.2, 1.3 |
| Spawn multiplo in un turno + esecuzione parallela, misurata | `coordinator.decompose` (`tool_choice:"any"`), `run_all_parallel` vs `run_all_sequential` | D1 / 1.3 |
| Structured output content/metadata, provenance preservata | `models.Finding` + `subagents` (tool senza campi fonte) + `synthesis` | D2/D5 / 2.1, 5.6 |
| Propagazione errori: timeout -> contesto strutturato, coverage gap | `sources.SourceTimeout`, `models.SubagentError`, `subagents` (ramo timeout), `coordinator.aggregate` | D5 / 5.3 |
| Conflitto fra fonti: entrambi i valori con attribuzione | `synthesis.synthesize` -> `ContestedClaim`, `models.SynthesisReport` | D5 / 5.6 |

## Come si lancia

Verifier deterministici (zero API, zero credito):
```
python verify_setup.py
python verify_subagents.py
python verify_coordinator.py
python verify_synthesis.py
```
Capstone: pipeline reale end-to-end (serve `.env` con `ANTHROPIC_API_KEY` + credito; ~4 chiamate):
```
python synthesis.py
```
Spike SDK (serve `pip install claude-agent-sdk`; usa l'auth di Claude Code / Pro):
```
python -u spike_agent_sdk.py
```

## Decisioni di design (il "perche'", per il ripasso teorico)

- **Provenance code-owned** (Card 18 riusata): il tool dei subagent espone solo `claim` + `evidence`;
  fonte/ref/data li timbra il codice dal fixture. Il modello e' *strutturalmente incapace* di
  sbagliare o inventare l'attribuzione.
- **Conflitto preservato, non risolto** (5.6): il tool di sintesi espone solo `status` + `note`; le
  posizioni in conflitto le ricostruisce il codice -> entrambi i valori sopravvivono per costruzione.
  La `data` tipizzata distingue *differenza temporale* da *contraddizione*.
- **Tre esiti distinti** (Card 5 / 5.3): `[]` (vuoto valido) e `SourceTimeout` (fallimento d'accesso)
  sono un valore-di-ritorno vs un'eccezione: fisicamente incapaci di collassare. Un timeout diventa
  un **coverage gap annotato**, non blocca il resto.
- **Orchestrazione in codice**: il turno unico del coordinator produce il *piano*; esecuzione e
  aggregazione sono deterministiche. Nessun `tool_result` rimandato al coordinator (nessun secondo giro).
- **Copertura piena vs partizione** (1.2): la demo assegna ogni sottotema a entrambi i subagent per far
  emergere il conflitto (duplicazione **voluta**). In un sistema a costo reale si partiziona; la
  duplicazione mirata e' l'eccezione giustificata (triangolare una metrica contesa).

## Trap Task -> Agent

La guida v1.0 dice `allowedTools: ["Task"]`. Il pacchetto reale (`claude-agent-sdk 0.2.147`) usa il
tool **`Agent`** (`allowed_tools=["Agent"]`); `Task` sopravvive solo nei record di init/denial per
retrocompat. **Sull'esame rispondi `Task`; nel codice reale e' `Agent`.** Confermato dallo spike:
`tool_use -> Agent`, `TaskStartedMessage`, delega avvenuta.

## Ambiente / versioni verificate

Python venv per progetto. `anthropic 1.1.0`, `pydantic 2.13.4`, `python-dotenv 1.2.3`,
`claude-agent-sdk 0.2.147`. Modello chiamate reali: `claude-haiku-4-5-20251001`, temperatura 0.