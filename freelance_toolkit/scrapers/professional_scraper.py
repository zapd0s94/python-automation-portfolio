import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import logging
from datetime import datetime
from pathlib import Path
import random

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("scraper_log.txt", encoding="utf-8"),
        logging.StreamHandler()
    ]
)
log = logging.getLogger(__name__)

CONFIG = {
    "base_url": "https://books.toscrape.com/catalogue/page-{}.html",
    "max_pages": 50,
    "delay_min": 1.0,
    "delay_max": 2.5,
    "max_retries": 3,
    "output_dir": "outputs",
    "user_agents": [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 Safari/605.1.15",
    ]
}

def get_headers():
    return {"User-Agent": random.choice(CONFIG["user_agents"])}

def fetch_page(url, retry=0):
    try:
        r = requests.get(url, headers=get_headers(), timeout=15)
        r.raise_for_status()
        log.info(f"OK [{r.status_code}] → {url}")
        return r
    except Exception as e:
        log.warning(f"Error: {e}")
        if retry < CONFIG["max_retries"]:
            time.sleep(5 * (retry + 1))
            return fetch_page(url, retry + 1)
        return None

def parse_products(soup):
    products = []
    items = soup.select("article.product_pod")
    log.info(f"Items encontrados en página: {len(items)}")
    
    for item in items:
        try:
            name = item.select_one("h3 a")["title"]
            price = float(
                item.select_one("p.price_color")
                .text.strip()
                .encode("ascii", "ignore")
                .decode()
                .replace("£", "")
                .replace("Â", "")
                .strip()
            )
            rating_map = {"One":1,"Two":2,"Three":3,"Four":4,"Five":5}
            rating = rating_map.get(item.select_one("p.star-rating")["class"][1], 0)
            availability = item.select_one("p.availability").text.strip()
            href = item.select_one("h3 a")["href"]
            href = href.replace("../", "")
            if not href.startswith("http"):
                href = "https://books.toscrape.com/catalogue/" + href

            products.append({
                "nombre": name,
                "precio_GBP": price,
                "precio_USD": round(price * 1.27, 2),
                "rating_estrellas": rating,
                "disponibilidad": availability,
                "url": href,
                "fecha_scraping": datetime.now().strftime("%Y-%m-%d %H:%M")
            })
        except Exception as e:
            log.warning(f"Error parseando item: {e}")
    return products

def save_results(data):
    Path(CONFIG["output_dir"]).mkdir(exist_ok=True)
    df = pd.DataFrame(data)
    df = df.drop_duplicates(subset=["nombre"])
    df = df.sort_values("precio_GBP")

    stats = pd.DataFrame([{
        "total_productos": len(df),
        "precio_minimo": df["precio_GBP"].min(),
        "precio_maximo": df["precio_GBP"].max(),
        "precio_promedio": round(df["precio_GBP"].mean(), 2),
        "rating_promedio": round(df["rating_estrellas"].mean(), 2),
        "generado": datetime.now().strftime("%Y-%m-%d %H:%M")
    }])

    filename = f"outputs/scraping_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    with pd.ExcelWriter(filename, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name="Productos", index=False)
        stats.to_excel(writer, sheet_name="Estadisticas", index=False)
        ws = writer.sheets["Productos"]
        for col in ws.columns:
            ws.column_dimensions[col[0].column_letter].width = min(
                max(len(str(c.value or "")) for c in col) + 4, 60
            )

    log.info(f"✓ Guardado: {filename} — {len(df)} productos únicos")
    return filename, df

def run_scraper():
    log.info("=" * 50)
    log.info("SCRAPER PROFESIONAL — INICIANDO")
    log.info("=" * 50)

    all_products = []

    for page in range(1, CONFIG["max_pages"] + 1):
        url = CONFIG["base_url"].format(page)
        log.info(f"Página {page}: {url}")

        response = fetch_page(url)
        if response is None:
            log.error(f"No se pudo acceder a página {page} — deteniendo")
            break

        soup = BeautifulSoup(response.text, "html.parser")
        products = parse_products(soup)
        all_products.extend(products)
        log.info(f"Total acumulado: {len(all_products)}")

        if not soup.select_one("li.next"):
            log.info("Última página alcanzada")
            break

        time.sleep(random.uniform(CONFIG["delay_min"], CONFIG["delay_max"]))

    if all_products:
        filename, df = save_results(all_products)
        log.info("=" * 50)
        log.info(f"COMPLETADO: {len(df)} productos")
        log.info(f"Precio mín: £{df['precio_GBP'].min()} | máx: £{df['precio_GBP'].max()}")
        log.info("=" * 50)
    else:
        log.error("Sin datos")

if __name__ == "__main__":
    run_scraper()