"""Clean raw_books.csv, convert GBP->INR at a fixed rate, load into SQLite.
Cleaning decisions:
  - price_gbp fails to parse -> median-impute within its category (missing
    price is likely a formatting glitch, not a real gap; categories are
    small so dropping rows would lose too much).
  - rating fails to parse -> drop the row (no sensible "typical" rating to
    impute for text that doesn't match any of the 5 known words at all).
Run: python clean_and_load.py
"""
import sqlite3
import pandas as pd

GBP_TO_INR_FIXED = 105.50  # fixed project baseline rate — the required, graded rate
RATING_MAP = {"One": 1, "Two": 2, "Three": 3, "Four": 4, "Five": 5}


def get_live_rate(fallback=GBP_TO_INR_FIXED):
    """Optional stretch only. Tries a free, keyless API for the current
    GBP->INR rate, checking the HTTP status code explicitly. Falls back to
    the fixed rate on any failure so price_inr is never left unset."""
    import requests
    try:
        resp = requests.get("https://open.er-api.com/v6/latest/GBP", timeout=5)
        if resp.status_code != 200:
            print(f"[live-rate] HTTP {resp.status_code} -> falling back to fixed rate.")
            return fallback
        rate = resp.json()["rates"]["INR"]
        print(f"[live-rate] Using live rate: 1 GBP = {rate} INR.")
        return rate
    except Exception as e:
        print(f"[live-rate] Request failed ({e}) -> falling back to fixed rate.")
        return fallback


def clean(raw_df, gbp_to_inr=GBP_TO_INR_FIXED):
    """Cleans the raw DataFrame, converts currencies, and imputes missing values."""
    df = raw_df.copy()
    df["price_gbp"] = pd.to_numeric(df["price_gbp_raw"].str.replace("£", "", regex=False), errors="coerce")
    df["rating"] = df["star_rating"].map(RATING_MAP)
    df["in_stock"] = df["availability_raw"].str.lower().str.contains("in stock")

    n_missing_price = df["price_gbp"].isna().sum()
    df["price_gbp"] = df.groupby("category")["price_gbp"].transform(lambda s: s.fillna(s.median()))
    df["price_gbp"] = df["price_gbp"].fillna(df["price_gbp"].median())

    n_before = len(df)
    df = df.dropna(subset=["rating"]).copy()
    df["rating"] = df["rating"].astype(int)
    print(f"Median-imputed price for {n_missing_price} row(s); dropped {n_before - len(df)} unparseable rating row(s).")

    df["price_inr"] = (df["price_gbp"] * gbp_to_inr).round(2)
    return df[["title", "price_gbp", "price_inr", "rating", "in_stock", "category"]]


def load_sqlite(df, db_path="books.db"):
    conn = sqlite3.connect(db_path)
    conn.executescript("""
        DROP TABLE IF EXISTS books;
        DROP TABLE IF EXISTS categories;
        CREATE TABLE categories (category_id INTEGER PRIMARY KEY AUTOINCREMENT, category_name TEXT UNIQUE NOT NULL);
        CREATE TABLE books (
            book_id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, price_gbp REAL, price_inr REAL,
            rating INTEGER CHECK (rating BETWEEN 1 AND 5), in_stock INTEGER CHECK (in_stock IN (0,1)),
            category_id INTEGER REFERENCES categories(category_id));
    """
    )
    conn.executemany("INSERT INTO categories (category_name) VALUES (?)",
                      [(c,) for c in sorted(df["category"].unique())])
    conn.commit()
    cat_ids = dict(conn.execute("SELECT category_name, category_id FROM categories").fetchall())
    conn.executemany(
        "INSERT INTO books (title, price_gbp, price_inr, rating, in_stock, category_id) VALUES (?,?,?,?,?,?)",
        [(r.title, r.price_gbp, r.price_inr, int(r.rating), int(r.in_stock), cat_ids[r.category])
         for r in df.itertuples(index=False)])
    conn.commit()
    conn.close()


if __name__ == "__main__":
    import sys

    # Scrape raw data
    print("Starting data scraping...")
    raw_books_df = scrape_books_toscrape(num_categories=3, min_books=60)
    print("Scraping complete.")

    # Determine currency conversion rate
    use_live = "--live-rate" in sys.argv
    rate = get_live_rate() if use_live else GBP_TO_INR_FIXED

    # Clean the scraped data
    print("Starting data cleaning...")
    cleaned_df = clean(raw_books_df, gbp_to_inr=rate)
    print("Cleaning complete.")

    # Save cleaned data to CSV
    cleaned_df.to_csv("books_clean.csv", index=False)
    print("Cleaned data saved to books_clean.csv")

    # Load cleaned data into SQLite
    print("Loading data into SQLite database...")
    load_sqlite(cleaned_df)
    print(f"Loaded {len(cleaned_df)} rows into books.db ({cleaned_df['category'].nunique()} categories). Rate: 1 GBP = {rate} INR.")