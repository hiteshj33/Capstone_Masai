"""Real scraper for books.toscrape.com. Works in Colab or locally — run:
    python scrape.py
On Colab, first cell: !git clone <repo-url> && %cd zepto/data_pipeline
"""
import sys, subprocess, pathlib
if "google.colab" in sys.modules:
    subprocess.run([sys.executable, "-m", "pip", "install", "-q", "-r",
                     str(pathlib.Path(__file__).parent / "requirements.txt")])

import csv, time
import requests
from bs4 import BeautifulSoup

BASE = "https://books.toscrape.com/catalogue/category/books/"
HEADERS = {"User-Agent": "Mozilla/5.0 (Zepto capstone scraper)"}
CATEGORIES = {"mystery_3": "Mystery", "travel_2": "Travel", "historical-fiction_4": "Historical Fiction"}


def scrape_category(slug, name, session):
    rows, url = [], f"{BASE}{slug}/index.html"
    while url:
        soup = BeautifulSoup(session.get(url, headers=HEADERS, timeout=15).text, "html.parser")
        for a in soup.select("article.product_pod"):
            title = a.h3.a["title"].strip()
            price = a.select_one("p.price_color").get_text(strip=True)
            rating = next(c for c in a.select_one("p.star-rating")["class"] if c != "star-rating")
            avail = a.select_one("p.instock.availability").get_text(strip=True)
            rows.append([title, price, rating, avail, name])
        nxt = soup.select_one("li.next a")
        url = url.rsplit("/", 1)[0] + "/" + nxt["href"] if nxt else None
        time.sleep(0.3)
    return rows


if __name__ == "__main__":
    all_rows = []
    with requests.Session() as s:
        for slug, name in CATEGORIES.items():
            rows = scrape_category(slug, name, s)
            print(f"{name}: {len(rows)} books")
            all_rows.extend(rows)

    with open("raw_books.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["title", "price_gbp_raw", "star_rating", "availability_raw", "category"])
        w.writerows(all_rows)
    print(f"Wrote raw_books.csv: {len(all_rows)} rows, {len(CATEGORIES)} categories.")
