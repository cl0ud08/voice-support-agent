"""
agent/graph.py

Builds the LangGraph state graph: defines nodes, edges, and compiles it
into a runnable object.

Run directly to test: python graph.py
"""

from langgraph.graph import StateGraph, START, END
from agent.state import AgentState
from agent.nodes import classify_node, respond_node


def build_graph():
    graph = StateGraph(AgentState)

    # Register nodes (give each a name, point it at the function)
    graph.add_node("classify", classify_node)
    graph.add_node("respond", respond_node)

    # Wire edges: START -> classify -> respond -> END
    graph.add_edge(START, "classify")
    graph.add_edge("classify", "respond")
    graph.add_edge("respond", END)

    return graph.compile()


if __name__ == "__main__":
    app = build_graph()

    test_inputs = [
    "What is my order status? My order ID is 1234",
    "Where is order 9999?",
    "I want a refund for my last purchase",
]
    for text in test_inputs:
        print(f"\n--- Running graph for: '{text}' ---")
        result = app.invoke({"user_input": text, "intent": None, "response": None})
        print(f"Final response: {result['response']}")