# CCAR-F — Decision Cards
 
Carte di decisione per la certificazione **Claude Certified Architect – Foundations**.
Formato tarato sull'esame: non "cos'è", ma **quando sì / quando no / cosa lo rompe /
il tradeoff** — le colonne su cui le domande scenario fanno scegliere.
 
> **Come usarle:** non rileggerle, *interrogale*. Copri la riga "anti-pattern" e
> ricostruiscila; oppure trasforma la card in una domanda scenario e rispondi.
> Ogni domanda di un mock è una di queste card vestita da scenario di produzione.
 
Ogni card è ancorata a un momento concreto costruito negli esercizi, così resta
un ricordo attaccato al concetto.
 
---
 
## Dominio 1 — Agentic Architecture & Orchestration
 
*(derivate dall'Esercizio 1 — service desk agent)*
 
### Card 1 — Terminazione del loop: `stop_reason`, non altro
 
- **Quando:** il criterio per continuare/uscire da un agentic loop è sempre
  `stop_reason` (`tool_use` = continua, `end_turn` = esci).
- **Anti-pattern:** decidere leggendo il testo dell'assistente ("sembra abbia
  finito"); usare un contatore di iterazioni *come logica di uscita*.
- **Cosa lo rompe:** un cap di iterazioni scambiato per meccanismo di controllo →
  l'agente si ferma a metà o gira su segnali sbagliati.
- **Tradeoff / sfumatura:** il cap va tenuto, ma **come rete di sicurezza**
  (guardrail), non come condizione. Distinguere i due è la trappola classica.
- **Visto:** il `while` che chiudeva su `end_turn` con `MAX_TURNS` come paracadute.
### Card 2 — Parallelo vs sequenziale
 
- **Quando parallelo:** più `tool_use` nello stesso turno, per tool
  **indipendenti** (identità + catalogo). Il loop deve iterare su *tutti* i blocchi
  ed eseguirli, restituendo tutti i `tool_result` in **un solo** messaggio `user`.
- **Quando sequenziale:** tool con **dipendenza** (l'entitlement ha bisogno
  dell'`employee_id` prodotto dall'identità) → si risolvono su turni successivi.
- **Cosa lo rompe:** assumere "un tool per turno" → perdi i risultati paralleli;
  oppure aspettarsi il parallelo tra due tool dipendenti → impossibile, al secondo
  manca l'input.
- **Tradeoff:** il parallelo riduce turni (meno latenza/token); il sequenziale è
  imposto dalla dipendenza, non scelto.
- **Visto:** turno 1 con tre tool insieme; `check_entitlement` che aspettava il turno 2.
### Card 3 — Enforcement deterministico vs prompt
 
- **Quando deterministico:** ogni volta che una regola **deve** valere su
  un'operazione critica/irreversibile (soglia di spesa, prerequisito d'identità).
  Vive in una guardia nel codice, su stato che controlli tu.
- **Quando il prompt basta:** orientamento, preferenze, comportamenti "best effort"
  dove un fallimento occasionale non fa danno.
- **Cosa lo rompe:** mettere la regola dura nel system prompt ("blocca sopra 500€")
  → livello probabilistico, tasso di fallimento non-zero → un giorno la salta.
- **Tradeoff:** la guardia costa codice e rigidità, ma è l'unica che *garantisce*.
  Il prompt è flessibile ma non garantisce nulla.
- **Sfumatura chiave d'esame:** la guardia deve **risolvere i fatti da sé** (il
  costo lo rilegge dal catalogo, non si fida del contesto del modello).
- **Visto:** `check_provisioning_allowed` che bloccava le 15 Copilot a prescindere.
### Card 4 — Descrizioni dei tool (routing)
 
- **Quando curarle:** sempre che esistano tool **simili** tra cui il modello può
  confondersi (catalogo vs entitlement). La descrizione è il meccanismo *primario*
  di selezione.
- **Cosa scrivere:** non solo cosa fa il tool, ma **quando usarlo *vs* l'alternativa**
  ("NON per X → usa l'altro"). Include boundary e dipendenze.
- **Cosa lo rompe:** descrizioni minime → il routing lo decide la parola dell'utente,
  non il confine del tool.
- **Tradeoff / limite:** descrizioni migliori *riducono* il misrouting ma non lo
  azzerano — restano probabilistiche. Quando la correttezza è obbligatoria, non ci
  si affida alla descrizione: si vincola (schema/enum) o si enforce.
- **Visto:** l'A/B in cui le descrizioni contrastive hanno portato il modello dallo
  "sceglie a naso" al "riconosce il confine e chiede".
### Card 5 — Risultato-vuoto-valido vs fallimento
 
- **Quando distinguere:** un tool che "non trova" deve dire *quale* non-trovato —
  nessun record (esito valido) vs errore d'accesso (fallimento). Contratti di ritorno
  coerenti (`{found: bool, value}`).
- **Cosa lo rompe:** collassare i due (un `None` ambiguo, o un errore per un vuoto
  legittimo) → il modello non sa se ritentare, chiedere, o concludere.
- **Tradeoff:** l'agente può *scegliere* di trattare "nessun record" come
  "non assegnato" — ma è una **decisione**, non un dato; va fatta consapevolmente.
- **Visto:** la scelta `{found: False}` distinto, e il modello che su Teams Premium
  ha *deciso* di leggerlo come "non ha accesso".
### Card 6 — Escalation: giudizio sopra la garanzia
 
- **Quando escalare:** richiesta esplicita di umano; **capability gap** (fuori scope
  dei tool: VPN, hardware) → inoltra, non improvvisare; operazione bloccata che
  richiede approvazione; nessun progresso.
- **Dove vive la decisione:** nel **modello** (è giudizio), guidata da criteri nel
  system prompt — non nel livello deterministico.
- **Cosa lo rompe:** far generare al modello una risposta best-effort fuori dai suoi
  strumenti (consigli di rete inventati); oppure mettere la *decisione* di escalare
  in una guardia rigida.
- **Tradeoff / robustezza:** la garanzia dura (blocco spesa) resta nella guardia;
  l'escalation aggiunge la *comunicazione* sopra. Se il modello dimentica di
  escalare, la garanzia regge lo stesso — il layering non dipende dal suo giudizio.
- **Handoff strutturato:** il contesto (reason categorizzato via `enum`, summary,
  id, prodotto) viaggia **negli argomenti** del tool, così non si perde nel passaggio.
- **Visto:** turno 3, VPN e Copilot escalati con le categorie giuste, accanto alla
  riga `BLOCCATO`.
---
 
## Dominio 3 — Claude Code Configuration & Workflows
 
*(derivate dall'Esercizio 2 — team development workflow)*
 
### Card 7 — Gerarchia e caricamento del contesto (CLAUDE.md)
 
- **Gli scope (broad→specific):** managed/enterprise (org-wide, non escludibile),
  project (`CLAUDE.md` alla root, versionato e condiviso), user (`~/.claude/`,
  personale, non condiviso), directory/subtree (in una sottocartella).
- **Come si combinano:** i file scoperti vengono **concatenati** in un unico
  contesto, ordinati broad→specific; l'ultimo letto ha peso *morbido* nei conflitti.
- **Anti-pattern / distrattore:** "il project *sovrascrive* lo user" come override
  secco → **falso**. È concatenazione con peso morbido, non una catena di precedenza.
  Solo managed policy è una fascia dura (non escludibile).
- **Caricamento:** all'avvio della sessione (il subtree si carica solo quando Claude
  legge file lì). Modifiche a caldo non si vedono finché non ricarichi.
- **Visto:** `/memory` con project "checked in" + user; la sezione `## Test` non
  "sentita" finché non ho riavviato la sessione.
### Card 8 — La config orienta, non garantisce (il filo rosso)
 
- **Il principio:** ogni livello di configurazione (CLAUDE.md, `.claude/rules/`,
  `allowed-tools` delle skill) **orienta** il modello con peso morbido; nessuno
  **garantisce** un comportamento. È la Card 3 vista dal lato config.
- **Quando basta la config:** convenzioni, preferenze, comportamenti best-effort
  dove un fallimento occasionale non fa danno.
- **Quando serve enforcement:** se un'azione deve/non-deve accadere a prescindere →
  **hook PreToolUse** o permessi (nell'Agent SDK `allowed-tools` non si applica
  proprio).
- **Cosa lo rompe / distrattore:** presentare CLAUDE.md, rules o `allowed-tools`
  come *garanzia* di sicurezza. Visto **tre volte** nello stesso esercizio.
- **Sfumatura:** l'agente pesa anche segnali non espliciti (es. la cronologia git
  del file) → rende i rifiuti "giusti" più probabili e argomentati, ma resta
  rinforzo probabilistico, non garanzia. Storia git pulita = segnale migliore.
- **Visto:** print infilati in `stubs.py` nonostante la regola; poi rifiuto motivato
  anche dal commit di revert; il warning `allowed-tools` sperimentale non enforced.
### Card 9 — Regole path-specific (`.claude/rules/`)
 
- **Quando:** istruzioni pertinenti solo a certi file → file in `.claude/rules/` con
  `paths` a glob; si caricano **on-demand**, solo quando Claude tocca un file che
  matcha, con la stessa priorità del CLAUDE.md ma senza competere sempre.
- **Perché:** risolve la **salienza** — una regola specifica caricata solo nel
  contesto giusto tiene meglio di una riga generica sepolta nel CLAUDE.md.
- **Sintassi / realtà:** i glob con `*` o `{` vanno **quotati** (YAML); se `paths:`
  non carica → fallback `globs:` (bug noto, fallimento silenzioso); path scoping solo
  a livello **progetto**, non user; i file rules non supportano import `@path`.
- **Design:** non duplicare — path-specific → rules; universale → CLAUDE.md.
- **Verifica:** **non** `/memory` (mostra i CLAUDE.md persistenti), ma la riga
  `Loaded ...file.md` che appare quando Claude legge il file che matcha. Contro-test
  in entrambe le direzioni.
- **Visto:** `Loaded stubs.md` su `stubs.py`, `agent.md` su `main_loop.py`; la
  rivincita sulla salienza (rifiuto dei print una volta che la regola era scoped).
### Card 10 — Skill e isolamento (`.claude/skills/`)
 
- **Quando:** workflow riusabile/on-demand → `.claude/skills/<nome>/SKILL.md`;
  **progressive disclosure** (solo la `description` sta in contesto finché non
  serve). Invocazione dal **nome della cartella**; `disable-model-invocation` /
  `user-invocable` controllano chi la lancia.
- **`context: fork`:** gira in un subagent **isolato** → il thread principale riceve
  solo il risultato, non il rumore. Non pesa sul contesto principale (`/context` non
  la conta → *prova* dell'isolamento; `/skills` la elenca come disponibile).
- **`allowed-tools`:** pre-approvazione **morbida**, non vincolo (3° caso Card 8);
  sperimentale, non enforced; nell'SDK non si applica.
- **La posizione è il meccanismo:** skill trovate solo in `.claude/skills/`; una
  cartella `skills/` fuori da `.claude/` è invisibile.
- **Sintassi:** valori con caratteri riservati YAML (`[ * {`) vanno quotati
  (es. `argument-hint: "[percorso-file]"`).
- **Visto:** `scenario-quiz` "Running in the background", `/context` resta a 16
  mentre `/skills` la mostra; il warning `github.copilot` era rumore di un'altra
  estensione, non un errore di Claude Code.
### Card 11 — MCP e scoping (`.mcp.json`)
 
- **Quando:** esporre tool a **qualsiasi** client (non solo al tuo script) → server
  MCP. Locale = **stdio** (sottoprocesso); remoto = HTTP. Config in `.mcp.json` alla
  root (project-scope, versionabile) vs local/user in `~/.claude.json`.
- **Concetto:** stesso "tool" dell'Esercizio 1 (nome/description/schema), ma vive in
  un **processo separato** che il client scopre e collega — diverso meccanismo di
  *distribuzione*, stesso concetto di tool.
- **Sicurezza / scoping:** niente segreti né path-macchina "duri" nel file condiviso
  → riferimenti a env var (`${CLAUDE_PROJECT_DIR:-.}`), credenziali via local-scope.
  Config condivisa (portabile) vs dettaglio di macchina (il `command` col python del
  venv, documentato per i colleghi).
- **Salvaguardia:** un `.mcp.json` committato può lanciare processi → approvazione
  **esplicita** all'avvio; scegliere "attuali" (non "attuali e futuri") mantiene la
  protezione sui server aggiunti in seguito.
- **Verifica:** `/mcp` per lo stato (connected/failed); si legge all'avvio (riavvia).
- **Visto:** `domain_weight` dal server `ccarf-quiz` risponde 27% pur non essendo in
  `tools.py`.
### Card 12 — Il debugging della configurazione (meta)
 
- **Si carica all'avvio:** per testare una modifica alla config (CLAUDE.md, rules,
  skill, server) **riavvia la sessione**. Le modifiche a caldo spesso non si vedono.
- **La posizione È il meccanismo:** rules solo in `.claude/rules/`, skill solo in
  `.claude/skills/`, config server in `.mcp.json` alla root. Un file nel posto
  sbagliato semplicemente non esiste per Claude Code.
- **Lo strumento di verifica giusto per ogni livello:** `/memory` (CLAUDE.md
  persistenti), riga `Loaded` (rules on-demand), `/skills` + `/context` (skill:
  disponibilità vs peso sul contesto), `/mcp` (server). Cercare la conferma nello
  strumento sbagliato inganna (es. `/context` non conta una skill forkata).
- **Le versioni cambiano:** API e sintassi di Claude Code e degli SDK cambiano in
  fretta (es. `mcp` 2.x: `FastMCP` → `MCPServer`) → leggi il traceback e i doc, non
  fidarti della memoria.
- **Versionare la config = scelta di scoping:** buca l'ignore di `.claude/` con
  eccezioni `!` per `rules/`, `skills/`, `mcp/` condivisi.
- **Visto:** skill invisibile perché fuori da `.claude/`; riavvii per far "sentire"
  CLAUDE.md e skill; correzione `FastMCP → MCPServer` letta dal traceback.
---
 
*Prossime sezioni (da riempire lungo il percorso): D2 Tool Design & MCP · D4 Prompt
Engineering & Structured Output · D5 Context Management & Reliability.*