import sqlite3
import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_DIR = os.path.join(BASE_DIR, "..", "database")
os.makedirs(DB_DIR, exist_ok=True)

DB_NAME = os.path.join(DB_DIR, "grocery_store.db")

def get_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def create_tables():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS products (
        product_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        price REAL NOT NULL,
        unit TEXT NOT NULL,
        stock REAL NOT NULL DEFAULT 0 CHECK(stock >= 0),
        discount REAL NOT NULL DEFAULT 0 CHECK(discount >= 0 AND discount <= 100)
    )
    """)
    
    # Check if stock column type is REAL
    cursor.execute("PRAGMA table_info(products)")
    columns = cursor.fetchall()
    stock_is_real = False
    for col in columns:
        if col['name'] == 'stock' and 'REAL' in col['type'].upper():
            stock_is_real = True
            break
            
    if not stock_is_real:
        print("Migrating products table to support REAL stock...")
        # Rename existing table
        cursor.execute("ALTER TABLE products RENAME TO products_old")
        
        # Create new table
        cursor.execute("""
        CREATE TABLE products (
            product_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            price REAL NOT NULL,
            unit TEXT NOT NULL,
            stock REAL NOT NULL DEFAULT 0 CHECK(stock >= 0),
            discount REAL NOT NULL DEFAULT 0 CHECK(discount >= 0 AND discount <= 100)
        )
        """)
        
        # Copy data
        cursor.execute("""
        INSERT INTO products (product_id, name, price, unit, stock, discount)
        SELECT product_id, name, price, unit, CAST(stock AS REAL), discount
        FROM products_old
        """)
        
        # Drop old table
        cursor.execute("DROP TABLE products_old")


    cursor.execute("""
    CREATE TABLE IF NOT EXISTS orders (
        order_id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_name TEXT,
        customer_address TEXT,
        order_date TEXT,
        total_amount REAL
    )
    """)
    
    
    try:
        cursor.execute("ALTER TABLE orders ADD COLUMN customer_address TEXT")
    except sqlite3.OperationalError:
        pass 
    
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS order_details (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id INTEGER,
        product_id INTEGER,
        quantity REAL,
        FOREIGN KEY(order_id) REFERENCES orders(order_id),
        FOREIGN KEY(product_id) REFERENCES products(product_id)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE,
        password_hash TEXT NOT NULL,
        role TEXT NOT NULL CHECK(role IN ('admin', 'customer'))
    )
    """)

    conn.commit()
    conn.close()
