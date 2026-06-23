from langgraph.types import interrupt
from core.state import ClinicalState


def human_review_node(state: ClinicalState) -> ClinicalState:
    """
    This node checks urgency. If emergent, it calls interrupt()
    which literally pauses the LangGraph execution and saves state
    to the checkpointer. The pipeline resumes only when /approve
    is called with the same thread_id.
    
    Non-emergent cases pass through silently with no interruption.
    """
    urgency = state.get("final_report", {}).get("urgency", "routine")

    if urgency == "emergent":
        print(f"EMERGENT case detected — pausing for human review")

        # interrupt() pauses execution here and returns to the caller
        # The value passed to interrupt() is sent back to the API
        # as the result of clinical_graph.invoke()
        human_decision = interrupt({
            "reason": "Emergent case requires doctor approval",
            "primary_diagnosis": state.get("final_report", {}).get("primary_diagnosis"),
            "urgency": urgency,
            "immediate_actions": state.get("final_report", {}).get("immediate_actions"),
        })

        # Execution resumes HERE after /approve is called
        approved = human_decision.get("approved", False)
        doctor_notes = human_decision.get("doctor_notes")

        if not approved:
            return {
                **state,
                "error": "Case rejected by reviewing doctor",
                "current_step": "rejected"
            }

        # Attach doctor notes to the final report
        final_report = state.get("final_report", {})
        if doctor_notes:
            final_report["doctor_notes"] = doctor_notes
            final_report["reviewed_by"] = "Human Doctor"

        return {
            **state,
            "final_report": final_report,
            "human_approved": True,
            "human_notes": doctor_notes,
            "current_step": "approved_by_human"
        }

    # Non-emergent — pass through
    return {**state, "current_step": "no_review_needed"}