import sqlite3
from pathlib import Path

import pandas as pd

SQL_AGENT_DIR = Path(__file__).resolve().parent
DB_PATH = SQL_AGENT_DIR / "db.sqlite"
CSV_PATH = SQL_AGENT_DIR / "products.csv"


def create_table(conn):
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS product (
            "index"        INTEGER,
            product_link   TEXT,
            title          TEXT,
            brand          TEXT,
            price          INTEGER,
            discount       REAL,
            avg_rating     REAL,
            total_ratings  INTEGER
        )
        """
    )
    conn.execute('CREATE INDEX IF NOT EXISTS ix_product_index ON product ("index")')


def seed_from_csv(conn):
    df = pd.read_csv(CSV_PATH)
    conn.execute("DELETE FROM product")
    df.to_sql("product", conn, if_exists="append", index=False)
    return len(df)


def main():
    if not CSV_PATH.exists():
        raise FileNotFoundError(
            f"Source CSV not found at {CSV_PATH}. "
            "Place a products.csv with columns (index, product_link, title, brand, "
            "price, discount, avg_rating, total_ratings) next to this script."
        )

    conn = sqlite3.connect(DB_PATH)
    create_table(conn)
    rows = seed_from_csv(conn)
    conn.commit()
    conn.close()
    print(f"SQL Agent DB seeded: {rows} products -> {DB_PATH}")


if __name__ == "__main__":
    main()
