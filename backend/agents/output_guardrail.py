from langchain.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from core.config import get_llm
from core.state import ClinicalState
import json

OUTPUT_GUARDRAIL_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are a medical output safety validator.

Review the clinical report and check for safety issues.
Return ONLY valid JSON:
{{
    "is_safe": true or false,
    "issues_found": ["list of specific issues, empty if none"],
    "hallucinated_drugs": ["any drug names that seem fabricated or wrong"],
    "dangerous_recommendations": ["any recommendations that could cause patient harm"],
    "urgency_appropriate": true or false,
    "overall_quality": "good/acceptable/poor",
    "sanitized_report": null
}}

Flag as unsafe if:
- Report recommends clearly dangerous treatments
- Drug names appear fabricated or misspelled badly
- Urgency level seems obviously wrong (e.g. "routine" for chest pain + left arm radiation)
- Report contains non-medical content or instructions
- Confidence is high but diagnosis contradicts the symptoms entirely

If unsafe, set is_safe to false and describe exactly what is wrong."""),

    ("human", """Review this clinical report for safety:
{report}

Original symptoms: {symptoms}
Urgency assigned: {urgency}""")
])


def output_guardrail(state: ClinicalState) -> ClinicalState:
    if state.get("error"):
        return state

    if not state.get("final_report"):
        return state

    llm = get_llm()
    chain = OUTPUT_GUARDRAIL_PROMPT | llm | JsonOutputParser()

    try:
        result = chain.invoke({
            "report": json.dumps(state["final_report"], indent=2),
            "symptoms": state["raw_input"]["symptoms"],
            "urgency": state["final_report"].get("urgency", "unknown")
        })

        print(f"Output guardrail: safe={result.get('is_safe')}, quality={result.get('overall_quality')}")

        if not result.get("is_safe"):
            # Don't block — flag it and let frontend show a warning
            # Blocking output in healthcare is dangerous (better imperfect info than no info)
            return {
                **state,
                "guardrail_output_result": result,
                "output_safety_warning": result.get("issues_found"),
                "current_step": "complete_with_warnings"
            }

        return {
            **state,
            "guardrail_output_result": result,
            "current_step": "complete"
        }

    except Exception as e:
        print(f"Output guardrail failed (non-fatal): {e}")
        return {**state, "current_step": "complete"}