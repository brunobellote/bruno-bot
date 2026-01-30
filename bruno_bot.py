# ==========================================
# BRUNO BOT v8 CLEAN (REBUILD TOTAL)
# estável + telegram sólido + decisões claras
# ==========================================

import time, json, os, ccxt
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import urllib3

urllib3.disable_warnings()

# =========================
# CONFIG
# =========================

TOKEN = "8004229528:AAGgqLNmXhslcYmhULVN40Q3X-zvj6Wd-6A"
CHAT_ID = "8335409471"
TIMEFRAME = "2h"

POSITIONS_FILE = "positions.json"
OFFSET_FILE = "offset.txt"

exchange = ccxt.bybit()

# =========================
# SESSION ESTÁVEL (MAC SAFE)
# =========================

session = requests.Session()

retry = Retry(total=5, backoff_factor=0.3)
adapter = HTTPAdapter(max_retries=retry)

session.mount("https://", adapter)


# =========================
# TELEGRAM
# =========================

def tg_get(url, **kw):
    return session.get(url, verify=False, headers={"Connection":"close"}, timeout=20, **kw)

def tg_post(url, **kw):
    return session.post(url, verify=False, headers={"Connection":"close"}, timeout=20, **kw)


def send(msg):
    try:
        import requests
        requests.post(
            f"https://api.telegram.org/bot{TOKEN}/sendMessage",
            data={"chat_id": CHAT_ID, "text": msg},
            timeout=10
        )
    except Exception as e:
        print("Telegram erro:", e)
# =========================
# OFFSET
# =========================

def load_offset():
    if os.path.exists(OFFSET_FILE):
        return int(open(OFFSET_FILE).read())
    return 0

def save_offset(x):
    open(OFFSET_FILE,"w").write(str(x))

last_id = load_offset()


# =========================
# POSITIONS
# =========================

def load_positions():
    if os.path.exists(POSITIONS_FILE):
        return json.load(open(POSITIONS_FILE))
    return []

def save_positions(p):
    json.dump(p, open(POSITIONS_FILE,"w"), indent=2)


# =========================
# UTILS
# =========================

def norm(s):
    s=s.upper().replace("/","")
    return s[:-4]+"/USDT"


# =========================
# ANALISE
# =========================

def analyze(symbol):

    try:
        ohlc = exchange.fetch_ohlcv(symbol, TIMEFRAME, limit=200)
    except:
        send("❌ símbolo inválido")
        return

    o = [x[1] for x in ohlc]
    h = [x[2] for x in ohlc]
    l = [x[3] for x in ohlc]
    c = [x[4] for x in ohlc]
    v = [x[5] for x in ohlc]

    price = c[-1]

    # ===== VOLUME =====
    buy  = sum(v[i] for i in range(-4,0) if c[i] > o[i])
    sell = sum(v[i] for i in range(-4,0) if c[i] < o[i])

    if buy > sell:
        bias = "LONG"
    elif sell > buy:
        bias = "SHORT"
    else:
        send("Sem dominância de volume")
        return

    # ===== SMA =====
    sma8  = sum(c[-8:])/8
    sma21 = sum(c[-21:])/21

    broke = price>sma21 if bias=="LONG" else price<sma21

    # ===== ATR =====
    atr = sum(h[i]-l[i] for i in range(-10,0))/10

    target = price + atr*2 if bias=="LONG" else price - atr*2
    stop   = price - atr   if bias=="LONG" else price + atr

    send(
f"""📊 {symbol}
Direção: {bias}

Entrada: {round(price,5)}
Stop: {round(stop,5)}
Alvo: {round(target,5)}
"""
    )


# =========================
# POSIÇÕES
# =========================

def check_positions():

    p=load_positions()

    if not p:
        send("Sem posições")
        return

    out="📊 POSIÇÕES\n\n"

    for pos in p:

        sym=pos["symbol"]
        entry=float(pos["entry"])
        size=float(pos["size"])
        lev=float(pos["lev"])
        side=pos["side"]

        price=exchange.fetch_ticker(sym)["last"]

        pnl=(price-entry)/entry
        if side=="SHORT":
            pnl=-pnl

        usd=pnl*size*lev

        out+=f"{sym} | {round(pnl*100,2)}% (${round(usd,2)})\n"

    send(out)


# =========================
# TELEGRAM LOOP
# =========================

def check_telegram():

    global last_id

    try:
        r = tg_get(
            f"https://api.telegram.org/bot{TOKEN}/getUpdates",
            params={"offset": last_id+1}
        ).json()
    except:
        return

    for u in r.get("result",[]):

        last_id=u["update_id"]
        save_offset(last_id)

        txt=u.get("message",{}).get("text","")
        parts=txt.split()

        if not parts:
            continue

        cmd=parts[0]

        if cmd=="/check" and len(parts)==2:
            analyze(norm(parts[1]))

        elif cmd=="/posicoes":
            check_positions()

        elif cmd=="/help":
            send("/check BTCUSDT | /posicoes")


# =========================
# MAIN
# =========================

send("🚀 Bruno Bot v8 CLEAN online")

while True:
    check_telegram()
    time.sleep(3)

