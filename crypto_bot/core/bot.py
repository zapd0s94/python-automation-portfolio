import ccxt, os, time
from dotenv import load_dotenv
from datetime import datetime

load_dotenv("crypto_bot/config/.env")

SYMBOL = "BTC/USDT"
GRID_LEVELS = 5
GRID_PCT = 0.005

exchange = ccxt.binance({
    "apiKey": os.getenv("BINANCE_KEY"),
    "secret": os.getenv("BINANCE_SECRET"),
    "enableRateLimit": True,
    "options": {"defaultType": "spot"},
})

exchange.set_sandbox_mode(True)
print("[PAPER MODE] Conectado al Testnet de Binance")

def get_price():
    ticker = exchange.fetch_ticker(SYMBOL)
    return ticker["last"]

def calcular_grid(precio_base):
    niveles = []
    for i in range(1, GRID_LEVELS + 1):
        buy  = round(precio_base * (1 - GRID_PCT * i), 2)
        sell = round(precio_base * (1 + GRID_PCT * i), 2)
        niveles.append({"nivel": i, "buy": buy, "sell": sell})
    return niveles

def log(msg):
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] {msg}")

def run():
    log("Bot iniciado — PAPER MODE")
    while True:
        try:
            precio = get_price()
            grid = calcular_grid(precio)
            log(f"BTC precio actual: ${precio:,.2f}")
            for n in grid:
                log(f"  Nivel {n['nivel']}: COMPRA ${n['buy']:,} | VENTA ${n['sell']:,}")
            log("--- esperando 60 segundos ---")
            time.sleep(60)
        except Exception as e:
            log(f"Error: {e}")
            time.sleep(30)

if __name__ == "__main__":
    run()