"""
data/seed_db.py

Creates a mock SQLite database of shipments for our courier/logistics
voice agent to query. Run this once to create/reset data/orders.db.

Run directly: python seed_db.py
"""

import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "orders.db")


def seed_database():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE shipments (
            tracking_id TEXT PRIMARY KEY,
            customer_name TEXT NOT NULL,
            status TEXT NOT NULL,
            current_location TEXT NOT NULL,
            items TEXT NOT NULL,
            estimated_delivery TEXT
        )
    """)

    mock_shipments = [
        ("1001", "Priya Sharma", "in transit", "Mumbai sorting facility", "Wireless Mouse", "2026-06-26"),
        ("1002", "Rahul Verma", "processing", "Delhi warehouse", "Mechanical Keyboard", "2026-06-30"),
        ("1003", "Ananya Gupta", "delivered", "Bengaluru — front door", "USB-C Hub", "2026-06-18"),
        ("1004", "Vikram Singh", "cancelled", "N/A", "Laptop Stand", None),
        ("1234", "Test User", "out for delivery", "Jaipur local hub", "Bluetooth Headphones", "2026-06-27"),
    ]

    cursor.executemany(
        "INSERT INTO shipments VALUES (?, ?, ?, ?, ?, ?)",
        mock_shipments,
    )

    conn.commit()
    conn.close()
    print(f"Seeded {len(mock_shipments)} shipments into {DB_PATH}")


if __name__ == "__main__":
    seed_database()