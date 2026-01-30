import re

with open("bruno_bot.py","r") as f:
    txt = f.read()

pattern = r"def send\(.*?\n\n"
replacement = """def send(msg):
    try:
        import requests
        requests.post(
            f"https://api.telegram.org/bot{TOKEN}/sendMessage",
            data={"chat_id": CHAT_ID, "text": msg},
            timeout=10,
            verify=False
        )
    except Exception as e:
        print("Telegram falhou:", e)

"""

txt = re.sub(pattern, replacement, txt, flags=re.S)

with open("bruno_bot.py","w") as f:
    f.write(txt)

print("✅ Função send corrigida automaticamente")
