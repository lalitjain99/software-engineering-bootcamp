import sqlite3

# Connect to database (or create it)
conn = sqlite3.connect("store.db")
cursor = conn.cursor()

# 1. Crucial: Enable foreign keys in SQLite
cursor.execute("PRAGMA foreign_keys = ON;")

cursor.execute("DROP TABLE IF EXISTS products;")
cursor.execute("DROP TABLE IF EXISTS stores;")

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

stores_to_insert = [
    ("Tech Superstore",),
    ("Fashion Hub",)
]

cursor.executemany(
    "INSERT INTO stores (name) VALUES (?)",
    stores_to_insert
)
# Commit changes 
conn.commit()


# --- STEP 2: Map Store Names to their SQLite-generated IDs ---
# Fetch all stores to see what IDs SQLite assigned them
cursor.execute("SELECT id, name FROM stores;")
store_rows = cursor.fetchall()

# Create a lookup dictionary: {"Tech Superstore": 1, "Fashion Hub": 2}
store_id_map = {name: store_id for store_id, name in store_rows}
print("Store ID Mapping:", store_id_map)

# --- STEP 3: Prepare Products Using the Dynamic Store IDs ---
# Notice we use the dictionary to look up the correct ID dynamically
products_to_insert = [
    (store_id_map["Tech Superstore"], "Wireless Mouse", "MS-901", 25.99),
    (store_id_map["Tech Superstore"], "Mechanical Keyboard", "KB-202", 79.99),
    (store_id_map["Fashion Hub"], "Cotton T-Shirt", "TS-505", 19.99),
    (store_id_map["Fashion Hub"], "Denim Jeans", "DJ-404", 49.99)
]


# --- STEP 4: Bulk Insert Products ---
cursor.executemany(
    """
    INSERT INTO products (store_id, name, sku, price) 
    VALUES (?, ?, ?, ?);
    """,
    products_to_insert
)

conn.commit()

# ==========================================
# 1. Attempt to insert a product with a duplicate SKU
# ==========================================
print("1. Testing Duplicate SKU...")
try:
    # "MS-901" already exists, and sku has a UNIQUE constraint
    cursor.execute(
        "INSERT INTO products (store_id, name, sku, price) VALUES (?, ?, ?, ?);",
        (store_id_map["Tech Superstore"], "Another Mouse", "MS-901", 29.99)
    )
    conn.commit()
except sqlite3.IntegrityError as e:
    print(f"Caught expected error (Duplicate SKU): {e}\n")


# ==========================================
# 2. Attempt to insert a product with a non-existent store_id
# ==========================================
print("2. Testing Non-Existent Store ID...")
try:
    # Store ID 999 does not exist, and foreign keys are enabled
    cursor.execute(
        "INSERT INTO products (store_id, name, sku, price) VALUES (?, ?, ?, ?);",
        (999, "Ghost Item", "GHOST-101", 15.00)
    )
    conn.commit()
except sqlite3.IntegrityError as e:
    print(f"Caught expected error (Foreign Key violation): {e}\n")

# ==========================================
# 3. List all products for store 1
# ==========================================
print(f"3. Listing products for store ID {store_id_map['Tech Superstore']}:")
cursor.execute("SELECT id, name, sku, price FROM products WHERE store_id = ?;", (store_id_map['Tech Superstore'],))
products = cursor.fetchall()
for p in products:
    print(f"   - Product: {p[1]} | SKU: {p[2]} | Price: ${p[3]}")
print()


# ==========================================
# 4. Use a JOIN to display each product with its store name
# ==========================================
print("4. Running JOIN Query (Products + Store Names):")
join_query = """
    SELECT p.name AS product_name, p.sku, s.name AS store_name 
    FROM products p
    JOIN stores s ON p.store_id = s.id;
"""
cursor.execute(join_query)
results = cursor.fetchall()
for row in results:
    print(f"   - {row[0]} ({row[1]}) is sold at {row[2]}")
print()


# ==========================================
# 5. Attempt to delete a store that still has products
# ==========================================
print("5. Testing Deletion Restriction...")
try:
    # Store ID 1 still has 'Wireless Mouse' attached, and ON DELETE RESTRICT is set
    cursor.execute("DELETE FROM stores WHERE id = ?;", (store_id_map['Tech Superstore'],))
    conn.commit()
except sqlite3.IntegrityError as e:
    print(f"Caught expected error (Cannot delete store with active products): {e}\n")

# Close connection
conn.close()