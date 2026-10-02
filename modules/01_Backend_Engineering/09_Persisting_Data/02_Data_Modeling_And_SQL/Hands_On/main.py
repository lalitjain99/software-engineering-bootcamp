import sqlite3

# Connect to database (or create it)
conn = sqlite3.connect("store.db")
cursor = conn.cursor()

# 1. Crucial: Enable foreign keys in SQLite
cursor.execute("PRAGMA foreign_keys = ON;")

# 2. Create the stores table
cursor.execute("""
CREATE TABLE IF NOT EXISTS stores (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL
);
""")

# 3. Create the products table
cursor.execute("""
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY,
    store_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    sku TEXT NOT NULL UNIQUE,
    price NUMERIC NOT NULL CHECK (price > 0),
    FOREIGN KEY (store_id)
        REFERENCES stores(id)
        ON DELETE RESTRICT
);
""")

# 4. Create the index (Must come AFTER the table is created)
cursor.execute("""
CREATE INDEX IF NOT EXISTS idx_products_store_id ON products(store_id);
""")

#5 insert data into store table

stores_data = [
    ("Downtown Electronics",),
    ("Uptown Fashion Hub",)
]

cursor.executemany(
    "INSERT INTO stores (name) VALUES (?)",
    stores_data
)
# Commit changes and close connection
conn.commit()
conn.close()