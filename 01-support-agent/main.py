import os
from dotenv import load_dotenv
import anthropic
from tools import TOOLS

load_dotenv()

client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
prompts = [
    "Quanto costa Copilot?",
    "alice@company.com ha già Copilot?",
    "Che situazione abbiamo con Power BI Pro per alice@company.com?",
    "Per alice@company.com, mi dici di Power BI Pro?",
    "Verifica Teams Premium per bob@company.com",
    "Info su Copilot"
]

for i, prompt in enumerate(prompts):    
    print("--- PROMPT ", i, " - ", prompt, " ---")

    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=512,
        tools=TOOLS,
        messages=[
            {"role": "user", "content":prompt}
            ],
    )

    print("stop_reason:", response.stop_reason)
    for block in response.content:
        print("blocco:", block.type)
        if block.type == "tool_use":
            print("  tool:", block.name)
            print("  input:", block.input)
        elif block.type == "text":
            print("  testo:", block.text)

    print("----")
    print()



