"""
data/order_lookup.py

Plain Python function to look up a shipment by tracking ID.
"""

import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "orders.db")


def get_shipment_status(tracking_id: str) -> dict:
    """Looks up a shipment by tracking ID. Returns a dict with shipment info, or an error."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(
        "SELECT tracking_id, customer_name, status, current_location, items, estimated_delivery "
        "FROM shipments WHERE tracking_id = ?",
        (tracking_id,),
    )
    row = cursor.fetchone()
    conn.close()

    if row is None:
        return {"found": False, "error": f"No shipment found with tracking ID {tracking_id}"}

    return {
        "found": True,
        "tracking_id": row[0],
        "customer_name": row[1],
        "status": row[2],
        "current_location": row[3],
        "items": row[4],
        "estimated_delivery": row[5],
    }


if __name__ == "__main__":
    print(get_shipment_status("1234"))
    print(get_shipment_status("9999"))