from langchain.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from core.config import get_llm
from core.state import ClinicalState
import json


DIAGNOSIS_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are an experienced clinical diagnostician.
Based on the structured patient case and retrieved medical evidence, generate a differential diagnosis.

Return ONLY a valid JSON object with exactly this structure, no extra text:
{{
    "differential_diagnosis": [
        {{
            "rank": 1,
            "condition": "condition name",
            "probability": "high/medium/low",
            "supporting_evidence": ["symptom or finding that supports this diagnosis"],
            "against_evidence": ["symptom or finding that argues against this diagnosis"],
            "cited_source": "source name from the evidence provided",
            "recommended_tests": ["test1", "test2"],
            "urgency": "emergent/urgent/routine"
        }}
    ],
    "primary_diagnosis": "single most likely diagnosis",
    "immediate_actions": ["action1", "action2"],
    "specialist_referral": "which specialist if needed, or null"
}}

Rules:
- Rank up to 4 differential diagnoses, most likely first
- Use ONLY the evidence provided, do not make up sources
- urgency emergent means needs attention within minutes
- urgency urgent means within hours
- urgency routine means can wait for scheduled appointment
- Be medically accurate and conservative"""),

    ("human", """Structured Patient Case:
{structured_case}

Retrieved Medical Evidence:
{evidence}

Generate differential diagnosis based on this data.""")
])


def diagnosis_agent(state: ClinicalState) -> ClinicalState:

    # Stop if any previous agent errored
    if state.get("error"):
        return state

    llm = get_llm()
    chain = DIAGNOSIS_PROMPT | llm | JsonOutputParser()

    # Format evidence into readable text for the prompt
    # We join all retrieved docs into one string
    evidence_text = "\n\n".join([
        f"[{e['condition']}] ({e['source']}): {e['content']}"
        for e in state["retrieved_evidence"]
    ])

    try:
        result = chain.invoke({
            # Convert structured_case dict to formatted JSON string
            # so LLM can read it clearly in the prompt
            "structured_case": json.dumps(state["structured_case"], indent=2),
            "evidence": evidence_text
        })

        print(f"Diagnosis agent done — primary: {result.get('primary_diagnosis')}")

        return {
            **state,
            "differential_diagnosis": result,
            "current_step": "diagnosis_complete"
        }

    except Exception as e:
        return {
            **state,
            "error": f"Diagnosis agent failed: {str(e)}",
            "current_step": "error"
        }