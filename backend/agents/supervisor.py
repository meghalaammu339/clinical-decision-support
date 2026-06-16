from langchain.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from core.config import get_llm
from core.state import ClinicalState

# LLM only used for the ambiguous retry decision after critique
RETRY_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are a clinical supervisor. A diagnosis has been critiqued.
Decide if the diagnosis needs revision.

Confidence score: {confidence_score}
Missed diagnoses flagged: {missed_diagnoses}
Loop count so far: {loop_count}

Rules:
- If loop_count >= 2, always respond: FINISH
- If confidence_score < 60 OR missed_diagnoses is non-empty, respond: diagnosis_agent
- Otherwise respond: FINISH

Respond with ONLY one word: diagnosis_agent or FINISH""")
])


def supervisor_node(state: ClinicalState) -> ClinicalState:
    """Deterministic routing for all pipeline stages.
    LLM is only called for the critique->diagnosis retry decision."""

    if state.get("error"):
        print("Supervisor decision: FINISH (error)")
        return {**state, "next_agent": "FINISH"}

    # Stage 1: risk not done yet
    # Use current_step to detect if risk ran (even if result is None due to failure)
    current_step = state.get("current_step", "starting")
    if current_step in ("starting", None) and state.get("risk_assessment") is None:
        print("Supervisor decision: risk_agent")
        return {**state, "next_agent": "risk_agent"}

    # Stage 2: intake not done
    if state.get("structured_case") is None:
        print("Supervisor decision: intake_agent")
        return {**state, "next_agent": "intake_agent"}

    # Stage 3: research not done
    if not state.get("retrieved_evidence"):
        print("Supervisor decision: research_agent")
        return {**state, "next_agent": "research_agent"}

    # Stage 4: diagnosis not done
    if state.get("differential_diagnosis") is None:
        print("Supervisor decision: diagnosis_agent")
        return {**state, "next_agent": "diagnosis_agent"}

    # Stage 5: critique not done
    if state.get("critique") is None:
        print("Supervisor decision: critique_agent")
        return {**state, "next_agent": "critique_agent"}

    # Stage 6: post-critique — LLM decides if retry is needed
    loop_count = state.get("loop_count", 0)
    if loop_count >= 2:
        print("Supervisor decision: FINISH (max loops reached)")
        return {**state, "next_agent": "FINISH"}

    llm = get_llm()
    chain = RETRY_PROMPT | llm | StrOutputParser()
    decision = chain.invoke({
        "confidence_score": state.get("confidence_score", 100),
        "missed_diagnoses": state.get("missed_diagnoses") or [],
        "loop_count": loop_count,
    }).strip()

    if decision not in ("diagnosis_agent", "FINISH"):
        decision = "FINISH"

    # Reset critique so the next loop goes through critique again
    if decision == "diagnosis_agent":
        print(f"Supervisor decision: diagnosis_agent (retry loop {loop_count + 1})")
        return {**state, "next_agent": "diagnosis_agent", "critique": None, "differential_diagnosis": None}

    print("Supervisor decision: FINISH")
    return {**state, "next_agent": "FINISH"}
