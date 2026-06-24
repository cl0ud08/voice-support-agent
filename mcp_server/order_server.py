"""
mcp_server/order_server.py

An MCP server exposing one tool: get_shipment_status.
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from mcp.server.fastmcp import FastMCP
from data.order_lookup import get_shipment_status as _get_shipment_status

mcp = FastMCP("shipment-server")


@mcp.tool()
def get_shipment_status(tracking_id: str) -> dict:
    """
    Look up the status of a customer's shipment by tracking ID.

    Args:
        tracking_id: The tracking ID to look up, e.g. "1234"
    """
    return _get_shipment_status(tracking_id)


if __name__ == "__main__":
    mcp.run()