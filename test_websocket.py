"""
test_websocket.py

A minimal WebSocket client to test our /ws/chat endpoint manually.
Run this while uvicorn is running in another terminal.
"""

import asyncio
import websockets
import json


async def test_chat():
    uri = "ws://127.0.0.1:8000/ws/chat"

    async with websockets.connect(uri) as websocket:
        test_messages = [
            "What is my order status? My order ID is 1234",
            "Where is order 9999?",
            "I want a refund",
        ]

        for msg in test_messages:
            print(f"\nSending: {msg}")
            await websocket.send(msg)

            response = await websocket.recv()
            data = json.loads(response)
            print(f"Received: {data}")


if __name__ == "__main__":
    asyncio.run(test_chat())