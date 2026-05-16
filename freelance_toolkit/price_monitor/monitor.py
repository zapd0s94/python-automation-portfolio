import requests
from bs4 import BeautifulSoup
import sqlite3
import smtplib
import random
import time
import logging
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
import os

load_dotenv()

# ── COLORES CONSOLA ──────────────────────────────────────────
R  = "\033[91m"   # rojo
G  = "\033[92m"   # verde
Y  = "\033[93m"   # amarillo
B  = "\033[94m"   # azul
C  = "\033[96m"   # cyan
W  = "\033[97m"   # blanco
BO = "\033[1m"    # bold
RE = "\033[0m"    # reset

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.FileHandler("monitor_log.txt", encoding="utf-8")]
)
log = logging.getLogger(__name__)

DB_NAME    = "prices.db"
CHECK_INTERVAL = 3600

PRODUCTS = [
    {"name": "A Light in the Attic",  "url": "https://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html",  "target_price": 55.00},
    {"name": "Tipping the Velvet",    "url": "https://books.toscrape.com/catalogue/tipping-the-velvet_999/index.html",     "target_price": 50.00},
    {"name": "Soumission",            "url": "https://books.toscrape.com/catalogue/soumission_998/index.html",             "target_price": 45.00},
    {"name": "Sharp Objects",         "url": "https://books.toscrape.com/catalogue/sharp-objects_997/index.html",          "target_price": 48.00},
    {"name": "Sapiens",               "url": "https://books.toscrape.com/catalogue/sapiens-a-brief-history-of-humankind_996/index.html", "target_price": 50.00},
]

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 Safari/605.1.15",
]

def banner():
    print(f"\n{B}{'═'*62}{RE}")
    print(f"{B}║{BO}{Y}   🔍 PRICE MONITOR BOT  ·  Professional Edition          {RE}{B}║{RE}")
    print(f"{B}║{C}   Automated price tracking & alert system                {RE}{B}║{RE}")
    print(f"{B}║{W}   github.com/zapd0s94/python-automation-portfolio         {RE}{B}║{RE}")
    print(f"{B}{'═'*62}{RE}\n")

def section(title):
    print(f"\n{B}┌{'─'*60}┐{RE}")
    print(f"{B}│{RE} {BO}{C}{title:<58}{RE} {B}│{RE}")
    print(f"{B}└{'─'*60}┘{RE}")

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS price_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_name TEXT,
        price REAL,
        currency TEXT,
        timestamp TEXT,
        url TEXT
    )''')
    conn.commit()
    conn.close()
    print(f"  {G}✓{RE} Database initialized — {W}{DB_NAME}{RE}")

def get_price(url):
    try:
        headers = {"User-Agent": random.choice(USER_AGENTS)}
        r = requests.get(url, headers=headers, timeout=15)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        price_text = soup.select_one("p.price_color").text.strip()
        price = float(
            price_text.encode("ascii", "ignore")
            .decode()
            .replace("£", "")
            .replace("Â", "")
            .strip()
        )
        return price
    except Exception as e:
        log.error(f"Error: {e}")
        return None

def save_price(product_name, price, url):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute(
        "INSERT INTO price_history (product_name, price, currency, timestamp, url) VALUES (?,?,?,?,?)",
        (product_name, price, "GBP", datetime.now().strftime("%Y-%m-%d %H:%M:%S"), url)
    )
    conn.commit()
    conn.close()

def get_price_history(product_name, limit=2):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute(
        "SELECT price, timestamp FROM price_history WHERE product_name=? ORDER BY timestamp DESC LIMIT ?",
        (product_name, limit)
    )
    rows = c.fetchall()
    conn.close()
    return rows

def send_alert(product_name, current_price, target_price, url):
    email    = os.getenv("ALERT_EMAIL")
    password = os.getenv("ALERT_PASSWORD")

    print(f"  {R}🚨 ALERT TRIGGERED:{RE} {BO}{product_name}{RE}")
    print(f"     Current:  {Y}£{current_price}{RE}  |  Target: £{target_price}  |  Saved: {G}£{round(target_price-current_price,2)}{RE}")
    print(f"     URL: {C}{url[:60]}...{RE}")

    if not email or not password:
        print(f"  {Y}⚠ Email not configured — alert shown in console only{RE}")
        log.warning(f"ALERT (console): {product_name} @ £{current_price}")
        return

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"🚨 Price Alert: {product_name} — £{current_price}"
    msg["From"]    = email
    msg["To"]      = email

    html = f"""
    <html><body style="font-family:Arial;background:#0D2137;color:white;padding:20px;">
      <div style="max-width:600px;margin:auto;background:#1565C0;border-radius:12px;padding:24px;">
        <h1 style="color:#F9A825;">🚨 Price Alert!</h1>
        <p><b>{product_name}</b> has reached your target price!</p>
        <table style="width:100%;background:#0D2137;border-radius:8px;padding:16px;">
          <tr><td>Current Price:</td><td style="color:#F9A825;font-size:24px;"><b>£{current_price}</b></td></tr>
          <tr><td>Your Target:</td><td>£{target_price}</td></tr>
          <tr><td>You Save:</td><td style="color:#4CAF50;">£{round(target_price-current_price,2)}</td></tr>
        </table>
        <a href="{url}" style="display:block;margin-top:16px;background:#F9A825;color:#0D2137;
           padding:12px;text-align:center;border-radius:8px;font-weight:bold;text-decoration:none;">
           🛒 Buy Now
        </a>
        <p style="font-size:11px;color:#90CAF9;margin-top:16px;">
          Price Monitor Bot © — github.com/zapd0s94/python-automation-portfolio
        </p>
      </div>
    </body></html>
    """
    msg.attach(MIMEText(html, "html"))
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(email, password)
            server.sendmail(email, email, msg.as_string())
        print(f"  {G}✓ Email alert sent to {email}{RE}")
        log.info(f"Email sent: {product_name} @ £{current_price}")
    except Exception as e:
        print(f"  {R}✗ Email error: {e}{RE}")

def check_prices():
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    section(f"PRICE CHECK  ·  {now}")

    results = []
    alerts  = 0

    print(f"\n  {'PRODUCT':<35} {'CURRENT':>10} {'TARGET':>10} {'STATUS':>12}  {'TREND':>6}")
    print(f"  {'─'*35} {'─'*10} {'─'*10} {'─'*12}  {'─'*6}")

    for product in PRODUCTS:
        price = get_price(product["url"])
        if price is None:
            print(f"  {R}✗{RE} {product['name']:<33} {'ERROR':>10}")
            continue

        save_price(product["name"], price, product["url"])
        history = get_price_history(product["name"], 2)

        # Trend
        trend = "  —  "
        if len(history) >= 2:
            prev = history[1][0]
            if price < prev:
                trend = f"{G}▼ £{round(prev-price,2)}{RE}"
            elif price > prev:
                trend = f"{R}▲ £{round(price-prev,2)}{RE}"

        # Status
        if price <= product["target_price"]:
            status = f"{G}✅ ALERT{RE}"
            alerts += 1
            send_alert(product["name"], price, product["target_price"], product["url"])
        else:
            diff = round(price - product["target_price"], 2)
            status = f"{Y}£{diff} above{RE}"

        name_short = product["name"][:33]
        print(f"  {W}{name_short:<35}{RE} {Y}£{price:>8.2f}{RE} {C}£{product['target_price']:>8.2f}{RE}  {status:<12}  {trend}")
        results.append(price)
        time.sleep(random.uniform(1, 2))

    # Summary
    print(f"\n  {B}{'─'*62}{RE}")
    print(f"  {BO}SUMMARY:{RE}  Products checked: {W}{len(results)}{RE}  |  Alerts triggered: {R if alerts else G}{alerts}{RE}  |  Avg price: {Y}£{round(sum(results)/len(results),2) if results else 0}{RE}")
    print(f"  {B}{'─'*62}{RE}\n")
    log.info(f"Check complete: {len(results)} products, {alerts} alerts")

def run_monitor():
    banner()
    section("INITIALIZING")
    init_db()
    print(f"  {G}✓{RE} Monitoring {W}{len(PRODUCTS)}{RE} products")
    print(f"  {G}✓{RE} Check interval: {W}{CHECK_INTERVAL//60} minutes{RE}")
    print(f"  {G}✓{RE} Alert method: {W}{'Email' if os.getenv('ALERT_EMAIL') else 'Console'}{RE}\n")

    while True:
        check_prices()
        print(f"  {C}⏰ Next check in {CHECK_INTERVAL//60} minutes  ·  Press Ctrl+C to stop{RE}\n")
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    run_monitor()