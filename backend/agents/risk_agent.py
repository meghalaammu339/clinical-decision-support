from langchain.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from core.config import get_llm
from core.state import ClinicalState

RISK_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are a clinical risk assessment specialist.
Calculate a patient risk score based on their profile.

Return ONLY valid JSON:
{{
    "risk_score": number 0-100,
    "risk_level": "low/moderate/high/critical",
    "risk_factors": ["list of risk factors"],
    "protective_factors": ["list of protective factors"],
    "risk_summary": "one sentence summary"
}}

Score guide: 0-25 low, 26-50 moderate, 51-75 high, 76-100 critical
Consider: age, gender, history, medications, symptoms, duration"""),

    ("human", """Symptoms: {symptoms}
Age: {age}
Gender: {gender}
Medical History: {medical_history}
Medications: {current_medications}
Duration: {duration}""")
])


def risk_agent(state: ClinicalState) -> ClinicalState:
    if state.get("error"):
        return state

    llm = get_llm()
    chain = RISK_PROMPT | llm | JsonOutputParser()
    raw = state["raw_input"]

    try:
        result = chain.invoke({
            "symptoms": raw["symptoms"],
            "age": raw["age"],
            "gender": raw["gender"],
            "medical_history": raw["medical_history"],
            "current_medications": raw["current_medications"],
            "duration": raw["duration"]
        })
        print(f"Risk agent done — score: {result.get('risk_score')}")
        return {**state, "risk_assessment": result, "current_step": "risk_complete"}
    except Exception as e:
        print(f"Risk agent failed (non-fatal): {e}")
        return {**state, "risk_assessment": {"risk_score": 0, "risk_level": "unknown", "risk_factors": [], "protective_factors": [], "risk_summary": "Risk assessment unavailable"}, "current_step": "risk_skipped"}