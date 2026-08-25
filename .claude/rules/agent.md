---
paths: ["**/main_loop.py", "**/agent*.py"]
---
# Regole per il loop agentico
- La terminazione del loop si decide su stop_reason (tool_use vs end_turn),
  mai leggendo il testo né con un contatore come logica primaria.
- Le operazioni critiche o irreversibili passano da una guardia deterministica,
  non dal solo prompt.