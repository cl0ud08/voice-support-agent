"""
agent/nodes.py

Each function here is a "node" in our graph for the courier/logistics
voice agent: classify intent, then respond using real shipment data.
"""

import os
import json
import re
from dotenv import load_dotenv
from groq import Groq
from agent.state import AgentState
from data.order_lookup import get_shipment_status

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise ValueError("Missing GROQ_API_KEY in .env")

client = Groq(api_key=GROQ_API_KEY)

MODEL = "llama-3.1-8b-instant"

VALID_INTENTS = ["shipment_status", "delivery_issue", "refund", "general"]

CLASSIFY_SYSTEM_PROMPT = f"""You classify courier/logistics customer support messages into exactly one intent.

Valid intents: {", ".join(VALID_INTENTS)}

- "shipment_status": the customer is asking where their package is, tracking, current location, or estimated delivery date
- "delivery_issue": the customer's package never arrived, is late, went to the wrong address, or was damaged
- "refund": the customer wants a refund or money back
- "general": anything else (greetings, unrelated questions, unclear requests)

Respond with ONLY a JSON object in this exact format, nothing else:
{{"intent": "shipment_status"}}
"""


def classify_node(state: AgentState) -> dict:
    """
    Sends user_input to Groq's LLM and gets back a structured intent classification.
    Falls back to "general" if the LLM call fails for any reason.
    """
    user_text = state["user_input"]

    try:
        completion = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": CLASSIFY_SYSTEM_PROMPT},
                {"role": "user", "content": user_text},
            ],
            temperature=0,
            max_tokens=50,
            response_format={"type": "json_object"},
        )
        raw = completion.choices[0].message.content
        parsed = json.loads(raw)
        intent = parsed.get("intent", "general")
        if intent not in VALID_INTENTS:
            intent = "general"
    except Exception as e:
        print(f"[classify_node] Groq call failed: {e} — defaulting to 'general'")
        intent = "general"

    print(f"[classify_node] input='{user_text}' -> intent='{intent}'")
    return {"intent": intent}


def respond_node(state: AgentState) -> dict:
    """
    Looks at the intent. For shipment_status, queries real shipment data
    (status, current location, estimated delivery) from the database.
    """
    intent = state["intent"]
    user_text = state["user_input"]

    if intent == "shipment_status":
        tracking_id = _extract_tracking_id(user_text)
        if tracking_id:
            result = get_shipment_status(tracking_id)
            if result["found"]:
                response = (
                    f"Your shipment {result['tracking_id']} ({result['items']}) "
                    f"is currently {result['status']}, last seen at {result['current_location']}."
                )
                if result["estimated_delivery"]:
                    response += f" Estimated delivery: {result['estimated_delivery']}."
            else:
                response = result["error"]
        else:
            response = "Could you share your tracking ID so I can look that up?"

    elif intent == "delivery_issue":
        response = (
            "I'm sorry to hear that. I've logged a delivery issue for your shipment — "
            "a support agent will follow up within 24 hours."
        )

    elif intent == "refund":
        response = "I can help you start a refund request for this shipment."

    else:
        response = "I'm not sure I understood that — could you rephrase?"

    print(f"[respond_node] intent='{intent}' -> response='{response}'")
    return {"response": response}


def _extract_tracking_id(text: str) -> str | None:
    """Pulls the first run of 3+ digits out of the text as a candidate tracking ID."""
    match = re.search(r"\d{3,}", text)
    return match.group(0) if match else None