from langchain.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from core.config import get_llm
from core.state import ClinicalState


INTAKE_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are a clinical intake specialist. 
Extract and structure the patient information from the input.

Return ONLY a valid JSON object with exactly this structure, no extra text:
{{
    "chief_complaint": "primary reason for visit in one sentence",
    "symptoms": ["list", "of", "individual", "symptoms"],
    "severity": "mild/moderate/severe",
    "symptom_duration": "duration as string",
    "age": number,
    "gender": "string",
    "medical_history": ["list", "of", "past", "conditions"],
    "current_medications": ["list", "of", "medications"],
    "red_flags": ["any urgent warning signs, empty list if none"],
    "search_keywords": ["3 to 5 keywords for medical literature search"]
}}

If any field is missing from input, use null for that field.
search_keywords should be medical terms useful for finding relevant literature."""),

    ("human", """Patient Information:
Symptoms: {symptoms}
Age: {age}
Gender: {gender}
Medical History: {medical_history}
Current Medications: {current_medications}
Duration: {duration}

Extract and return structured JSON.""")
])


def intake_agent(state: ClinicalState) -> ClinicalState:
    llm = get_llm()

    # LCEL chain — prompt | llm | parser
    # JsonOutputParser automatically parses LLM output string into Python dict
    chain = INTAKE_PROMPT | llm | JsonOutputParser()

    raw = state["raw_input"]

    try:
        structured = chain.invoke({
            "symptoms": raw["symptoms"],
            "age": raw["age"],
            "gender": raw["gender"],
            "medical_history": raw["medical_history"],
            "current_medications": raw["current_medications"],
            "duration": raw["duration"]
        })

        print(f"Intake agent done — chief complaint: {structured.get('chief_complaint')}")

        return {
            **state,                            # keep everything already in state
            "structured_case": structured,      # add our output
            "current_step": "intake_complete"   # update pipeline tracker
        }

    except Exception as e:
        # If anything fails, write error to state — graph will stop pipeline
        return {
            **state,
            "error": f"Intake agent failed: {str(e)}",
            "current_step": "error"
        }