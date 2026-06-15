from typing import TypedDict, Optional, List


class PatientCase(TypedDict):
    # Raw input from the user
    symptoms: str
    age: int
    gender: str
    medical_history: str
    current_medications: str
    duration: str


class ClinicalState(TypedDict):
    # The original user input
    raw_input: PatientCase

    # Intake agent fills this — structured version of raw input
    structured_case: Optional[dict]

    # RAG agent fills this — list of relevant medical docs retrieved
    retrieved_evidence: Optional[List[dict]]

    # Diagnosis agent fills this — the differential diagnosis
    differential_diagnosis: Optional[dict]

    # Critique agent fills these — final validated output
    critique: Optional[str]
    final_report: Optional[dict]

    # Pipeline control — tracks current step and any errors
    error: Optional[str]
    current_step: Optional[str]
    confidence_score: Optional[int]
    risk_assessment: Optional[dict]