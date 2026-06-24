"""
agent/state.py

Defines the shape of data that flows through our LangGraph nodes.
Every node receives this state, can read from it, and returns updates to it.
"""

from typing import TypedDict, Optional


class AgentState(TypedDict):
    """
    The shared state object passed between every node in the graph.

    - user_input: the raw text from the user (from Whisper transcription)
    - intent: what we think the user wants (filled in by classify_node)
    - response: the final text reply (filled in by respond_node)
    """
    user_input: str
    intent: Optional[str]
    response: Optional[str]