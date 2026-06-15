from langgraph.graph import StateGraph, END
from core.state import ClinicalState
from agents.intake_agent import intake_agent
from agents.rag_agent import rag_agent
from agents.diagnosis_agent import diagnosis_agent
from agents.critique_agent import critique_agent
from agents.risk_agent import risk_agent


def should_continue(state: ClinicalState) -> str:
    if state.get("error"):
        print(f"Pipeline stopping due to error: {state['error']}")
        return "end"
    return "continue"


def build_graph():
    graph = StateGraph(ClinicalState)

    graph.add_node("node_risk", risk_agent)
    graph.add_node("node_intake", intake_agent)
    graph.add_node("node_rag", rag_agent)
    graph.add_node("node_diagnosis", diagnosis_agent)
    graph.add_node("node_critique", critique_agent)

    graph.set_entry_point("node_risk")

    # Risk is non-fatal — always continues even if it fails
    graph.add_edge("node_risk", "node_intake")

    graph.add_conditional_edges("node_intake", should_continue,
        {"continue": "node_rag", "end": END})
    graph.add_conditional_edges("node_rag", should_continue,
        {"continue": "node_diagnosis", "end": END})
    graph.add_conditional_edges("node_diagnosis", should_continue,
        {"continue": "node_critique", "end": END})

    graph.add_edge("node_critique", END)
    return graph.compile()


clinical_graph = build_graph()