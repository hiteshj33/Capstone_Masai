# Data Pipeline

Scrapes books.toscrape.com → cleans/types fields → converts GBP→INR at a fixed rate →
loads into normalized SQLite → queries with SQL and pandas.

## Run — local

```bash
pip install -r requirements.txt
python scrape.py          # real live scrape (or: python seed_data.py, no internet needed)
python clean_and_load.py  # -> books.db
python queries.py
```

## Run — Google Colab

```python
!git clone <your-repo-url>
%cd zepto-data-ai-platform/data_pipeline
!python scrape.py
!python clean_and_load.py
!python queries.py
```
(`scrape.py` auto-installs its requirements on Colab; no separate `pip install` cell needed.)

## Design decisions

- **`scrape.py` vs `seed_data.py`:** `scrape.py` is the real `requests`+`BeautifulSoup`
  scraper (3 categories: Mystery, Travel, Historical Fiction — 63 books). `seed_data.py`
  is an offline fallback with the same real titles/prices/categories, for networks that
  can't reach books.toscrape.com; star ratings there are a deterministic hash since the
  site itself says ratings are random/meaningless. Both write the same CSV schema, so
  everything downstream is unaffected by which one you run.
- **Cleaning:** a `price_gbp` that fails to parse is median-imputed *within its category*
  (likely a formatting glitch, and categories are small enough that dropping would lose
  too much). A `rating` that fails to parse (matches none of the five known words) is
  dropped instead — there's no sensible "typical" value to impute there.
- **Currency:** fixed baseline **1 GBP = 105.50 INR** — a project-defined constant, not a
  live rate.
- **Schema:** `categories(category_id PK, category_name)` ↔ `books(book_id PK, ..., category_id FK)`.
- **Queries:** 5 required SQL clauses (SELECT/WHERE, ORDER BY/LIMIT, DISTINCT, IN/BETWEEN,
  JOIN) plus a `pd.merge`-only reproduction of the JOIN, confirmed identical to
  `pd.read_sql`'s result.

Full query output: `query_output.txt` (generate with `python queries.py > query_output.txt`).
