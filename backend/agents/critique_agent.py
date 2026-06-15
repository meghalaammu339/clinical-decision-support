from langchain.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from core.config import get_llm
from core.state import ClinicalState
import json


CRITIQUE_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are a senior medical consultant performing critical review of a diagnosis.

Your job:
1. Check if any important conditions were missed
2. Flag dangerous assumptions or blind spots  
3. Verify red flags were properly addressed
4. Validate urgency levels are appropriate
5. Produce a clean final consolidated report

Return ONLY a valid JSON object with exactly this structure, no extra text:
{{
    "critique_summary": "2-3 sentence overall assessment of diagnosis quality",
    "missed_diagnoses": ["conditions that should have been considered but weren't, empty list if none"],
    "concerns": ["specific concerns or flags, empty list if none"],
    "confidence_score": a number between 0 and 100,
    "final_report": {{
        "summary": "2-3 sentence clinical summary of the case",
        "primary_diagnosis": "final confirmed or revised primary diagnosis",
        "differential_list": ["ranked list of differentials as strings"],
        "immediate_actions": ["prioritized action list"],
        "recommended_tests": ["ordered list of investigations"],
        "specialist_referral": "referral recommendation or null",
        "urgency": "emergent/urgent/routine",
        "follow_up": "follow up recommendation",
        "disclaimer": "This is an AI-assisted decision support tool. All clinical decisions must be made by a qualified healthcare professional."
    }}
}}

Be thorough but concise. Patient safety is the priority."""),

    ("human", """Original Patient Case:
{structured_case}

Differential Diagnosis Generated:
{differential_diagnosis}

Medical Evidence Used:
{evidence}

Perform critical review and generate final report.""")
])


def critique_agent(state: ClinicalState) -> ClinicalState:

    # Stop if any previous agent errored
    if state.get("error"):
        return state

    llm = get_llm()
    chain = CRITIQUE_PROMPT | llm | JsonOutputParser()

    # Summarize evidence — we don't need full content here
    # just enough for the critique agent to know what sources were used
    evidence_summary = "\n".join([
        f"[{e['condition']}] from {e['source']}"
        for e in state["retrieved_evidence"]
    ])

    try:
        result = chain.invoke({
            "structured_case": json.dumps(state["structured_case"], indent=2),
            "differential_diagnosis": json.dumps(state["differential_diagnosis"], indent=2),
            "evidence": evidence_summary
        })

        print(f"Critique agent done — confidence: {result.get('confidence_score')}")

        return {
            **state,
            "critique": result.get("critique_summary"),
            "confidence_score": result.get("confidence_score"), 
            "final_report": result.get("final_report"),
            "current_step": "complete"
        }

    except Exception as e:
        return {
            **state,
            "error": f"Critique agent failed: {str(e)}",
            "current_step": "error"
        }