from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from core.state import ClinicalState
from agents.risk_agent import risk_agent
from agents.intake_agent import intake_agent
from agents.research_agent import research_agent, research_tool_node, extract_evidence_from_messages
from agents.diagnosis_agent import diagnosis_agent
from agents.critique_agent import critique_agent
from agents.supervisor import supervisor_node
from agents.input_guardrail import input_guardrail
from agents.output_guardrail import output_guardrail


def route_after_input_guardrail(state: ClinicalState) -> str:
    if state.get("error", "").startswith("INPUT_BLOCKED"):
        return "blocked"
    return "continue"

def route_after_supervisor(state: ClinicalState) -> str:
    return state["next_agent"]


def route_after_research(state: ClinicalState) -> str:
    last = state["messages"][-1]
    return "call_tools" if getattr(last, "tool_calls", None) else "extract_evidence"


def increment_loop(state: ClinicalState) -> ClinicalState:
    return {**state, "loop_count": state.get("loop_count", 0) + 1}

#place we defne node and edges

def build_graph():
    graph = StateGraph(ClinicalState)
    graph.add_node("input_guardrail", input_guardrail)
    graph.add_node("output_guardrail", output_guardrail)

    graph.add_node("supervisor", supervisor_node)
    graph.add_node("risk_agent", risk_agent)
    graph.add_node("intake_agent", intake_agent)
    graph.add_node("research_agent", research_agent)
    graph.add_node("call_tools", research_tool_node)
    graph.add_node("extract_evidence", extract_evidence_from_messages)
    graph.add_node("diagnosis_agent", diagnosis_agent)
    graph.add_node("critique_agent", critique_agent)
    graph.add_node("loop_tracker", increment_loop)

    graph.set_entry_point("input_guardrail")

    graph.add_conditional_edges("input_guardrail", route_after_input_guardrail, {
        "blocked": END,
        "continue": "supervisor",
    })

    graph.add_conditional_edges("supervisor", route_after_supervisor, {
        "risk_agent": "risk_agent",
        "intake_agent": "intake_agent",
        "research_agent": "research_agent",
        "diagnosis_agent": "diagnosis_agent",
        "critique_agent": "critique_agent",
        "FINISH": "output_guardrail",
    })

    graph.add_edge("risk_agent", "supervisor")
    graph.add_edge("intake_agent", "supervisor")

    graph.add_conditional_edges("research_agent", route_after_research, {
        "call_tools": "call_tools",
        "extract_evidence": "extract_evidence",
    })
    graph.add_edge("call_tools", "research_agent")
    graph.add_edge("extract_evidence", "supervisor")

    graph.add_edge("diagnosis_agent", "supervisor")
    graph.add_edge("critique_agent", "loop_tracker")
    graph.add_edge("loop_tracker", "supervisor")
    graph.add_edge("output_guardrail", END)
    checkpointer = MemorySaver()
    return graph.compile(checkpointer=checkpointer)


clinical_graph = build_graph()
