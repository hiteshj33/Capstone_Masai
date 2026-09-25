"""5 required SQL queries + pd.read_sql / pd.merge equivalence check.
Run: python queries.py
"""
import sqlite3
import pandas as pd

conn = sqlite3.connect("books.db")

QUERIES = {
    "SELECT/WHERE - under GBP 15": "SELECT title, price_gbp FROM books WHERE price_gbp < 15;",
    "ORDER BY/LIMIT - top 10 priciest": "SELECT title, price_gbp FROM books ORDER BY price_gbp DESC LIMIT 10;",
    "DISTINCT - categories": "SELECT DISTINCT category_name FROM categories ORDER BY category_name;",
    "IN/BETWEEN - rated 4-5, GBP 20-40": "SELECT title, rating, price_gbp FROM books WHERE rating IN (4,5) AND price_gbp BETWEEN 20 AND 40;",
}
JOIN_SQL = """
    SELECT c.category_name, b.title, b.rating, b.price_gbp
    FROM books b JOIN categories c ON b.category_id = c.category_id
    WHERE b.rating = (SELECT MAX(b2.rating) FROM books b2 WHERE b2.category_id = b.category_id)
    ORDER BY c.category_name, b.price_gbp;
"""
QUERIES["JOIN - top-rated per category"] = JOIN_SQL

if __name__ == "__main__":
    for label, sql in QUERIES.items():
        print(f"\n== {label} ==\n{sql.strip()}")
        print(pd.read_sql(sql, conn).head(10).to_string(index=False))

    # Reproduce the JOIN with pd.merge only (no SQL)
    books, cats = pd.read_sql("SELECT * FROM books", conn), pd.read_sql("SELECT * FROM categories", conn)
    merged = pd.merge(books, cats, on="category_id")
    top = merged[merged["rating"] == merged.groupby("category_id")["rating"].transform("max")]
    top = top[["category_name", "title", "rating", "price_gbp"]].sort_values(["category_name", "price_gbp"]).reset_index(drop=True)

    sql_result = pd.read_sql(JOIN_SQL, conn).sort_values(["category_name", "price_gbp"]).reset_index(drop=True)
    print(f"\npd.read_sql JOIN == pd.merge-only JOIN? {sql_result.equals(top)}")

    conn.close()
