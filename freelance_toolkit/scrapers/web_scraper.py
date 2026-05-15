import requests
from bs4 import BeautifulSoup
import pandas as pd

def scrape_site(url, css_selector, output_file="resultado.csv"):
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    try:
        r = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(r.text, "html.parser")
        items = soup.select(css_selector)
        data = [{"texto": item.get_text(strip=True), "href": item.get("href", "")} for item in items]
        df = pd.DataFrame(data)
        df.to_csv(output_file, index=False, encoding="utf-8")
        print(f"✓ {len(df)} items encontrados → guardado en {output_file}")
        return df
    except Exception as e:
        print(f"Error: {e}")
        return None

if __name__ == "__main__":
    df = scrape_site(
        "https://books.toscrape.com",
        "article.product_pod h3 a",
        "libros.csv"
    )
    print(df.head(5))