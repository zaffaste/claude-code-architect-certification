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
### Card 23 — Contesto esplicito ai subagent (non ereditano)
 
- **Quando:** ogni subagent gira in una chiamata isolata — non eredita la conversazione del
  coordinator, il prompt deve portare tutto il contesto necessario esplicitamente.
- **Cosa lo rompe:** assumere che il subagent "sappia" il topic generale perché è nella stessa
  run — senza contesto esplicito produce claim scollegati.
- **Tradeoff:** ricostruire il prompt da zero per ogni subagent costa ripetizione/token, ma è
  l'unico modo per garantire che l'isolamento non perda informazione.
- **Visto:** `subagents.build_prompt` (`subagents.py:46-53`, commento "il subagent riceve tutto
  qui, non eredita niente"); `verify_subagents.py` (verde).
### Card 24 — Spawn multiplo in un turno + trap Task→Agent
 
- **Quando:** il coordinator deve dispatchare più subagent nello stesso turno —
  `tool_choice:"any"` senza `disable_parallel_tool_use`, così il modello può emettere più
  `tool_use` insieme.
- **Cosa lo rompe:** nell'Agent SDK il tool per delegare si chiama `Agent`, non `Task` — un
  `allowed_tools` sbagliato blocca la delega silenziosamente.
- **Tradeoff:** il dispatch multiplo aumenta il parallelismo ma rende l'orchestrazione meno
  prevedibile (il numero di eventi nello spike varia run-to-run: 27 messaggi osservati in
  questa sessione, non un valore fisso).
- **Visto:** `coordinator.py:125` `tool_choice={"type":"any"}` senza
  `disable_parallel_tool_use`; `DISPATCH_TOOL` enum (`coordinator.py:26-38`);
  `verify_coordinator.py` (6 assignment da 6 dispatch, verde); `spike_agent_sdk.py`
  (`allowed_tools=["Agent"]`, commento "IL TRAP"): log reale con `tool_use → Agent`,
  `TaskStartedMessage`, "Delega a subagent avvenuta: True", 27 messaggi in questa run.
### Card 25 — Parallelo vs sequenziale: I/O-bound → thread, si misura
 
- **Quando:** subagent indipendenti che aspettano I/O vanno lanciati in thread paralleli — ma
  va misurato, non assunto.
- **Cosa lo rompe:** assumere che il parallelismo aiuti senza un numero a supporto.
- **Tradeoff:** i thread aggiungono complessità di orchestrazione per un guadagno che va
  giustificato.
- **Visto:** `coordinator.run_all_parallel` (`ThreadPoolExecutor`, `coordinator.py:82-88`);
  `verify_coordinator.py` misura seq=0.73s vs par=0.12s (par < seq/2, verde).
### Card 29 — Decomposizione a menu vincolato; copertura piena vs partizione, duplicazione
mirata come eccezione
 
- **Quando:** il coordinator assegna sottotemi a canali (web/doc) — vincolare le scelte a un
  enum (agent, subtopic) invece di testo libero garantisce che ogni dispatch sia valido a
  prescindere dal giudizio del modello.
- **Cosa lo rompe:** lasciare "agent"/"subtopic" liberi → il modello potrebbe inventare canali
  o sottotemi fuori fixture, rompendo l'aggregazione a valle.
- **Tradeoff:** il menu vincolato limita la flessibilità (non si può saltare/inventare un
  sottotema), ma rende `aggregate()` deterministico e testabile. Assegnare OGNI sottotema a
  ENTRAMBI i canali è una duplicazione mirata (non economica in chiamate) che garantisce
  copertura piena invece di una partizione rischiosa.
- **Visto:** `coordinator.COORD_SYSTEM` (`coordinator.py:40-52`, istruisce "OGNI sottotema a
  ENTRAMBI i subagent"); `DISPATCH_TOOL` enum su `agent`/`subtopic` (`coordinator.py:26-38`);
  `verify_coordinator.py`: 6 assignment da 6 dispatch (verde).
### Card 30 (opzionale) — Substrato: SDK reale vs orchestrazione a mano
 
- **Quando:** prototipare/misurare con precisione (timeout iniettati, conflitti costruiti,
  timing deterministico) richiede il controllo diretto del loop → orchestrazione a mano. L'SDK
  reale serve quando serve delega "vera", non il controllo di ogni dettaglio del mondo
  simulato.
- **Cosa lo rompe:** usare l'SDK reale per un test che deve restare deterministico — introduce
  non-determinismo (numero di messaggi variabile, 27 in questa run) e costo/latenza reale.
- **Tradeoff:** l'orchestrazione a mano costa più codice ma è gratis, deterministica, testabile
  senza rete; l'SDK reale costa meno codice ma meno controllo, zero determinismo.
- **Visto:** l'intera pipeline (`sources`/`subagents`/`coordinator`/`synthesis`, tutti i
  `verify_*.py` deterministici, zero chiamate rete tranne le call cognitive stub) vs
  `spike_agent_sdk.py` (chiamata reale, log non deterministico osservato).
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

## Dominio 2 — Tool Design & MCP Integration

*(derivate dagli Esercizi 1–3)*

### Card 13 — `tool_choice`: i quattro modi, e cosa cambia col forzato

- **I modi:** `auto` (il modello decide se chiamare un tool — default con tool presenti),
`any` (deve chiamare *un* tool, sceglie quale), `tool` (deve chiamare *quello* nominato),
`none` (nessun tool — default senza tool).
- **Quando `tool`/`any`:** quando l'output *deve* essere strutturato (estrazione,
classificazione). `tool` se lo schema è uno solo e noto; `any` se hai più schemi e il
tipo di documento è incerto.
- **La sfumatura che l'esame nasconde:** con `tool` o `any` l'API **prefilla** il messaggio
dell'assistente → il modello **non emette testo né ragionamento** prima del blocco
`tool_use`. Conseguenza: (1) niente scratchpad per ragionare prima di estrarre (se serve,
un campo "reasoning" come prima proprietà, o non forzare); (2) con un solo tool forzato la
`description` **smette di fare da router** — resta solo istruzione su *come* riempire.
- **Cosa lo rompe:** aspettarsi una spiegazione a parole insieme al tool forzato; o credere
che la description "selezioni" quando c'è un solo tool obbligato.
- **Visto:** l'estrazione ticket con `tool_choice: {"type":"tool", ...}` che restituiva solo
il blocco `tool_use`, mai testo.

### Card 14 — Il contratto d'errore: categorie + `isRetryable`

- **Le categorie:** `transient` (timeout, servizio giù), `validation` (input malformato),
`business` (violazione di policy), `permission`. Un errore generico ("operazione fallita")
impedisce all'agente di decidere il recupero.
- **La chiave è `isRetryable`, non la categoria:** ciò che conta è *ritentare o no*.
Ritentabile = errore di **forma/struttura** (schema, chiave omessa, enum errato): il feedback
specifico lo corregge. Non ritentabile = **contenuto assente o conflitto**: ripresentare lo
stesso input non fa comparire un dato mancante né riconcilia un conflitto reale.
- **Cosa lo rompe:** un loop che ritenta *tutto* → spreca chiamate su buchi di contenuto
(anti-pattern Task 2.2); o collassare "accesso fallito" e "vuoto valido" (Card 5).
- **Tradeoff / onestà:** "assente" vs "mal-letto" spesso non è distinguibile dall'output —
classificare i buchi di contenuto come non-ritentabili accetta un raro route inutile in
cambio di non sprecare retry.
- **Visto:** `check()` che marcava l'enum errato `retryable=True` (→ RETRY) e il mancato
identificativo `retryable=False` (→ ROUTE); il loop che convergeva sul primo e instradava
subito il secondo.

### Card 15 — Scoping `.mcp.json`: project vs user (angolo D2)

- **La decisione:** tooling condiviso di team → `.mcp.json` alla root (project-scope,
versionato); server personali/sperimentali o con credenziali → `~/.claude.json` (user-scope,
non condiviso).
- **Perché è D2 e non solo D3:** è una scelta di *distribuzione del tool* — chi vede quale
tool — non solo di config di Claude Code.
- **Cosa lo rompe:** credenziali o path-macchina "duri" nel file condiviso; committare un
server senza approvazione esplicita all'avvio.
- **Visto:** vedi Card 11 per il meccanismo (`ccarf-quiz`, `${CLAUDE_PROJECT_DIR}`); qui
l'angolo è la scelta di scope come design del tool.

### Card 27 — Provenance code-owned: il tool non espone fonte/data

- **Quando:** il modello genera solo claim+evidence; provenance (fonte, data) resta fuori dal
suo controllo, iniettata dal codice dopo la chiamata — stessa logica di Card 18 (il gate
finanziario non si fida del numero estratto dal modello).
- **Cosa lo rompe:** far scrivere al modello anche source_name/source_ref nel tool — apre alla
provenance inventata o disallineata.
- **Tradeoff:** il modello ha meno flessibilità (non arricchisce la citazione), ma la
provenance resta garantita corretta perché non passa mai dalla sua generazione.
- **Visto:** `subagents.FINDING_TOOL` espone solo `claim`+`evidence_excerpt`
(`subagents.py:23-37`, required a riga 35); `verify_subagents.py`: "espone solo claim+evidence;
provenance fuori dalla portata del modello" (verde).

---

## Dominio 4 — Prompt Engineering & Structured Output

*(derivate dall'Esercizio 3 — pipeline di estrazione)*

### Card 16 — Structured output: garantisce la forma, non la semantica

- **Cosa garantisce:** `tool_use` + JSON schema elimina gli errori di *sintassi* — output
sempre parsabile e conforme allo schema.
- **Cosa NON garantisce:** la *correttezza*. Un JSON perfetto può essere semanticamente
sbagliato — valore nel campo errato, numeri che non tornano, un placeholder al posto di
`null`. La validazione di schema passa lo stesso, perché è forma valida.
- **Cosa lo rompe:** trattare "schema conforme" come "estrazione corretta" → falsa sicurezza.
È la Card 3/8 vista da D4.
- **Nota esame vs realtà:** la guida insegna `tool_use` (Task 4.3) — la risposta d'esame. Ma
nel mondo reale esiste lo **structured output nativo GA** (`output_config.format`,
constrained decoding). Tieni entrambe le letture: rispondere "nativo" all'esame sbaglia
l'item; insegnare solo `tool_use` in Reti è arretrato.
- **Visto:** `"<UNKNOWN>"` che passava la validazione perché stringa valida; e l'`unit_cost`
inventato che rendeva la somma = totale dichiarato.

### Card 17 — Nullable, placeholder e il confine dell'interpretazione

- **Nullable contro la fabbricazione:** un campo che *può mancare* va `nullable`, o il modello
inventa un valore per soddisfare un `required` non-null. Ma nullable **permette** null, non lo
**impone**.
- **Il modello riempie comunque:** su campi stringa, senza istruzione, mette placeholder
(`"<UNKNOWN>"`) invece di `null`. Serve la regola esplicita ("se assente → null, niente
segnaposto").
- **La regola dura over-corregge:** "non dedurre" rischia di azzerare anche interpretazioni
legittime (idiomi: "un paio" → 2). Il **few-shot calibra il confine** che la prosa non sa
fissare — mostri cosa è interpretazione accettabile e cosa è invenzione, invece di accumulare
divieti.
- **Misurato (vedi Card 22):** in un A/B su tre ticket il few-shot ha dato delta zero — input
già a soffitto per il baseline. Il giudizio di design resta valido (il few-shot è la leva
corretta per il confine quando serve), ma qui resta *disponibile, non attivo*: nessun gap
misurato da colmare in questo corpus.
- **Cosa lo rompe:** credere che nullable basti; o irrigidire il prompt finché sopprime anche
il buono.
- **Visto:** il baseline con `"<UNKNOWN>"`; la regola null che lo sistemava; gli esempi
few-shot con "un paio → 2" accanto a "budget/5 → unit_cost null".

### Card 18 — Consistency-check e input indipendenti

- **Il principio:** un controllo di coerenza è *teatro* se i due valori confrontati non sono
**indipendenti**. Confrontare `stated_total` con una somma calcolata su `unit_cost`
**prodotti dal modello** non verifica nulla — misura solo che il modello sa moltiplicare.
- **Sul denaro:** un valore monetario estratto è una *dichiarazione* del ticket, mai verità.
Ogni decisione finanziaria (il gate €500) risolve i prezzi da una **fonte autorevole** (il
catalogo, keyed sul prodotto), non dal numero nel campo. Se il gate legge dal catalogo, non
importa più che il modello abbia inventato l'unitario.
- **Cosa lo rompe:** far controllare il modello dal modello; lasciare che l'estrazione diventi
la fonte di verità per una decisione di soldi.
- **Visto:** `validation.check()` non confronta `stated_total_eur` con nessuna fonte
indipendente — un item con `unit_cost_eur` coerente con la quantità e il totale dichiarato
passa senza errori, qualunque sia l'origine del prezzo unitario (verificato eseguendo
`check()` su un caso sintetico: `unit_cost_eur=100, quantity=2, stated_total_eur=200` →
nessun issue). È la Card 3 applicata all'estrazione.

### Card 19 — Validation-retry: cosa ritenta e cosa no

- **Ritentabile = forma:** errori di schema/struttura (chiave omessa, enum errato). Il feedback
con l'errore *specifico* li corregge. Structured output li rende rari → il ramo retry è un
paracadute, non il protagonista.
- **Non ritentabile = contenuto:** informazione assente, o conflitto reale tra valori presenti.
Ripresentare lo stesso documento non aiuta → route a umano, **senza sprecare retry**.
- **Il cap è rete di sicurezza, non logica d'uscita:** si esce sulla *validazione* (valido /
non-retryable / budget finito); il contatore evita solo il loop infinito (Card 1 sul retry).
- **Cosa lo rompe:** un loop che ritenta tutto; invertire l'ordine dei rami (retry prima dei
non-retryable) sprecando chiamate.
- **Visto:** il loop dove enum-errato→buono convergeva in 2 attempt e no-identificativo
instradava subito; il feedback via `tool_result` con `is_error`.

---

## Dominio 5 — Context Management & Reliability

*(derivate dall'Esercizio 3 — batch, routing, misura)*

### Card 20 — Batch: la collisione che riscrive l'architettura

- **Quando:** volume alto, latenza-tollerante (report notturni, audit). Async, finestra ≤24h,
**nessun SLA**, −50%, fino a 100k request. **Non** per lavori bloccanti (pre-merge).
- **La collisione:** il batch **non supporta tool calling multi-turn** dentro una request →
ogni request è **one-shot** → il retry loop (multi-turn) **non può viverci**. Il loop sincrono
diventa una **pipeline multi-batch**: la validazione avviene sui risultati, i falliti diventano
un **secondo batch**, e il feedback **migra da `tool_result` a testo nel prompt**.
- **`custom_id` correla** risultato→richiesta: l'ordine non è garantito, quindi accoppiare per
posizione è un bug.
- **SLA math:** peggior caso = intervallo tra sottomissioni + finestra → **intervallo ≤ SLA −
finestra**. Se finestra ≥ SLA, il batch da solo non basta.
- **Cosa lo rompe:** infilare il retry loop dentro la request batch; correlare per ordine; usare
il batch per un flusso che aspetta la risposta.
- **Visto:** `run_batch_pipeline` dove l'errore batch → resubmit e lo schema errato → rebatch
con feedback, mai un retry inline; l'attesa senza SLA lanciando `batch.py`.

### Card 21 — Confidence: calibrata, non creduta; stratificata, non aggregata

- **La contraddizione, sciolta:** Task 5.2 dice che la confidence auto-riportata è inaffidabile;
Task 5.5 dice di usarla. La chiave è *calibrated using labeled validation sets*: il "0.9" non
vale 90% — va **misurato** su un set etichettato, per campo e tipo-documento.
- **L'aggregato maschera:** un 91% complessivo può nascondere un segmento al 65%. Si
**stratifica** per tipo-documento e campo → la soglia di routing è **per-segmento**, non globale.
- **Tre segnali, non uno:** i controlli deterministici e l'ambiguità dichiarata vengono *prima*;
la confidence del modello è il segnale più debole (auto-riportato), arriva per ultima e solo
dopo calibrazione.
- **Cosa lo rompe:** tagliare la confidence grezza a una soglia inventata; fidarsi
dell'aggregato; una soglia unica globale.
- **L'onestà che è la lezione:** senza corpus etichettato la calibrazione **non esiste** — il
vero primo passo è *costruire il validation set*, non aggiungere un campo confidence.
- **Visto:** i dati sintetici dove ≥0.90 dava 97.5% su prosa e 65% su tabella, con l'aggregato
che lo nascondeva — esempio illustrativo discusso in conversazione durante lo studio di questa
card, non prodotto da codice in questo repo. Resta perché fissa bene l'intuizione
dell'aggregato-che-maschera; il passo reale, se servisse davvero misurare, è costruire il
validation set etichettato (vedi sopra).

### Card 22 — La misura batte l'intuizione (metodologia)

- **Il principio:** su un sistema non-deterministico, una singola osservazione non prova nulla.
Un A/B a n=1 dove il baseline "funziona pure lui" è **inconcludente** — non distingue "la leva
serve" da "il baseline ha azzeccato".
- **Zero eventi ≠ nessun problema:** la *regola del tre* dà un limite superiore ~3/N (0/10 →
fino a ~30% reale). L'assenza di prova non è prova d'assenza.
- **Casi facili e aggregati ingannano:** su input a soffitto il base è già al massimo → ogni
leva di prompt mostra delta zero, e non riuscire a costruire uno stimolo che la faccia vincere
è *esso stesso un dato*.
- **Conseguenza operativa:** le leve (few-shot, regole di prompt) si aggiungono su **gap
misurato**, non preventivamente — metterle "per completezza" è costo a beneficio zero
(over-engineering, punito nei Sample Q2/Q3).
- **Cosa lo rompe:** concludere da una run; mettere in produzione una leva mai misurata;
fermarsi all'aggregato.
- **Visto:** l'A/B della regola null a 0/10 su entrambe; il few-shot con delta zero su tre
ticket; la decisione di tenere few-shot "disponibile ma non attivo" (vedi Card 17 per il
giudizio di design sul few-shot come leva del confine).

### Card 26 — Errore strutturato ≠ vuoto-valido; coverage gap annotato, non blocca

- **Quando:** `retrieve()` distingue "nessuna fonte trovata" (lista vuota, esito valido) da
"timeout/accesso fallito" (`SourceTimeout`, eccezione) — il coordinator li aggrega
diversamente.
- **Cosa lo rompe:** trattare un timeout come "zero risultati" silenzioso — il gap sembrerebbe
una scelta invece di un fallimento d'accesso da segnalare.
- **Tradeoff:** annotare i `coverage_gaps` invece di bloccare la pipeline lascia procedere la
sintesi con dati parziali — corretto per un research assistant, sbagliato per una decisione
finanziaria (vedi Card 5/14).
- **Visto:** i tre esiti di `sources.retrieve` (`sources.py:72-79`); `coordinator.aggregate`
(`coordinator.py:98-115`, distingue "fonte non disponibile (timeout)" da "nessuna fonte
trovata"); `verify_subagents.py`, `verify_coordinator.py`, `verify_synthesis.py` (tutti verdi).

### Card 28 — Conflitto preservato, non risolto; data tipizzata → temporale ≠ contraddizione

- **Quando:** due fonti autorevoli danno esiti opposti sullo stesso sottotema in anni diversi —
il sistema preserva entrambe le posizioni, non fa "vincere" una sintesi; la differenza di data
può spiegare la divergenza.
- **Cosa lo rompe:** far scegliere al modello quale fonte è "giusta" (bias/allucinazione);
ignorare le date e trattare la divergenza come rumore da appiattire.
- **Tradeoff:** preservare il conflitto costa una sintesi meno "pulita", ma è l'unica scelta
onesta quando i dati sono davvero in disaccordo.
- **Visto:** `synthesis.SYNTHESIS_TOOL` espone solo `status` (enum established/contested)+`note`
(`synthesis.py:24-38`); `verify_synthesis.py`: 2 posizioni preservate, fonti e anni
[2023, 2024], nota temporale presente (verde); `published_date` tipizzato `date` (coercizione
str→date in `models.py`, confermata da `verify_setup.py`).

---

*Prossime sezioni (da riempire lungo il percorso): altre card dagli esercizi successivi.*