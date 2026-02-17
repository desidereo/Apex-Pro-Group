import sqlite3
import datetime
import logging

DB_NAME = "orders.db"

def get_connection():
    return sqlite3.connect(DB_NAME)

def init_db():
    """Initialize the database with the necessary table."""
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            stripe_customer_id TEXT,
            stripe_subscription_id TEXT UNIQUE,
            tv_username TEXT,
            mt5_account_number TEXT,
            product_id TEXT,
            status TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    # Migration for existing DBs (try to add column if missing)
    try:
        c.execute("ALTER TABLE orders ADD COLUMN mt5_account_number TEXT")
    except sqlite3.OperationalError:
        pass # Column likely already exists
    
    conn.commit()
    conn.close()
    logging.info("Database initialized.")

def add_order(stripe_customer_id, stripe_subscription_id, tv_username, mt5_account_number, product_id, status="active"):
    """Add a new order to the database."""
    conn = get_connection()
    c = conn.cursor()
    try:
        c.execute('''
            INSERT INTO orders (stripe_customer_id, stripe_subscription_id, tv_username, mt5_account_number, product_id, status)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (stripe_customer_id, stripe_subscription_id, tv_username, mt5_account_number, product_id, status))
        conn.commit()
        logging.info(f"Order added: {tv_username or mt5_account_number} ({stripe_subscription_id})")
    except sqlite3.IntegrityError:
        logging.warning(f"Order already exists for subscription: {stripe_subscription_id}")
    finally:
        conn.close()

def check_mt5_license(mt5_account, product_id):
    """Check if an MT5 account has an active license for a product."""
    conn = get_connection()
    c = conn.cursor()
    # Check for active subscription matching account and product
    # We use LIKE for product_id in case you have variations, or exact match
    c.execute('''
        SELECT status FROM orders 
        WHERE mt5_account_number = ? 
        AND product_id = ? 
        AND status = 'active'
    ''', (mt5_account, product_id))
    row = c.fetchone()
    conn.close()
    return row is not None

def get_user_by_subscription(stripe_subscription_id):
    """Retrieve user details by subscription ID."""
    conn = get_connection()
    c = conn.cursor()
    c.execute('SELECT tv_username, product_id, stripe_customer_id FROM orders WHERE stripe_subscription_id = ?', (stripe_subscription_id,))
    row = c.fetchone()
    conn.close()
    if row:
        return {"tv_username": row[0], "product_id": row[1], "stripe_customer_id": row[2]}
    return None

def get_user_by_customer_id(stripe_customer_id):
    """Retrieve user details by Customer ID (returns most recent active if multiple)."""
    conn = get_connection()
    c = conn.cursor()
    # Assuming we want the latest active subscription for this customer
    c.execute('''
        SELECT tv_username, product_id, stripe_subscription_id 
        FROM orders 
        WHERE stripe_customer_id = ? AND status = 'active'
        ORDER BY created_at DESC LIMIT 1
    ''', (stripe_customer_id,))
    row = c.fetchone()
    conn.close()
    if row:
        return {"tv_username": row[0], "product_id": row[1], "stripe_subscription_id": row[2]}
    return None

def update_order_status(stripe_subscription_id, new_status):
    """Update the status of an order."""
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
        UPDATE orders 
        SET status = ?, updated_at = CURRENT_TIMESTAMP 
        WHERE stripe_subscription_id = ?
    ''', (new_status, stripe_subscription_id))
    conn.commit()
    conn.close()
    logging.info(f"Updated status for {stripe_subscription_id} to {new_status}")
