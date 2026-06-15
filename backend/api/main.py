from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
from core.graph import clinical_graph
from langchain.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from core.config import get_llm
import json
import requests as http_requests


app = FastAPI(
    title="Clinical Decision Support API",
    version="1.0.0"
)

# CORS — allows React (localhost:5173) to call this API
# Without this browser blocks the request
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Pydantic model — validates incoming request body
# FastAPI automatically returns 422 if any field is wrong type
class PatientCaseRequest(BaseModel):
    symptoms: str
    age: int
    gender: str
    medical_history: str
    current_medications: str
    duration: str


class DiagnosisResponse(BaseModel):
    status: str
    current_step: Optional[str]
    structured_case: Optional[dict]
    differential_diagnosis: Optional[dict]
    final_report: Optional[dict]
    critique: Optional[str]
    error: Optional[str]
    confidence_score: Optional[int]
    risk_assessment: Optional[dict]   # ADD THIS


class FollowUpRequest(BaseModel):
    question: str
    report: dict


class DrugCheckRequest(BaseModel):
    medications: List[str]

FOLLOWUP_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are a medical AI assistant helping a user understand a clinical diagnosis report.
    
You have access to the full clinical report. Answer the user's question clearly and in simple language.
Be accurate, concise, and always remind the user to consult a real doctor for medical decisions.
 
Clinical Report:
{report}"""),
    ("human", "{question}")
])
 
 
def get_followup_chain():
    llm = get_llm()
    return FOLLOWUP_PROMPT | llm | StrOutputParser()

@app.get("/health")
def health_check():
    # Simple endpoint to check if API is running
    return {"status": "healthy"}


@app.post("/followup")
async def followup(request: FollowUpRequest):
    try:
        chain = get_followup_chain()
        answer = chain.invoke({
            "report": json.dumps(request.report, indent=2),
            "question": request.question
        })
        return {"answer": answer}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/drug-interactions")
async def drug_interactions(request: DrugCheckRequest):
    meds = request.medications
    if len(meds) < 2:
        return {"interactions": [], "message": "Need at least 2 medications"}

    interactions = []
    for i in range(len(meds)):
        for j in range(i + 1, len(meds)):
            drug1 = meds[i].split()[0]
            drug2 = meds[j].split()[0]
            try:
                resp = http_requests.get(
                    "https://api.fda.gov/drug/event.json",
                    params={
                        "search": f'patient.drug.medicinalproduct:"{drug1}"+AND+patient.drug.medicinalproduct:"{drug2}"',
                        "limit": 1
                    },
                    timeout=8
                )
                total = resp.json().get("meta", {}).get("results", {}).get("total", 0)
                if total > 100:
                    interactions.append({
                        "drug1": drug1,
                        "drug2": drug2,
                        "severity": "high" if total > 1000 else "moderate",
                        "reports": total,
                        "message": f"{total} adverse event reports found"
                    })
            except:
                continue

    return {"interactions": interactions, "message": f"Checked {len(meds)} medications"}


@app.post("/analyze", response_model=DiagnosisResponse)
async def analyze_patient(request: PatientCaseRequest):

    # Build initial state — this is what gets passed to first agent
    initial_state = {
        "raw_input": request.model_dump(),  # converts pydantic model to dict
        "structured_case": None,
        "retrieved_evidence": None,
        "differential_diagnosis": None,
        "critique": None,
        "final_report": None,
        "error": None,
        "current_step": "starting"
    }

    try:
        # Run the full 4-agent pipeline
        # This is synchronous — waits for all agents to complete
        result = clinical_graph.invoke(initial_state)

        # If pipeline stopped due to error, raise HTTP 500
        if result.get("error"):
            raise HTTPException(
                status_code=500,
                detail=result["error"]
            )

        return DiagnosisResponse(
            status="success",
            current_step=result.get("current_step"),
            structured_case=result.get("structured_case"),
            differential_diagnosis=result.get("differential_diagnosis"),
            final_report=result.get("final_report"),
            confidence_score=result.get("confidence_score"), 
            critique=result.get("critique"),
            error=None,
            risk_assessment=result.get("risk_assessment")

        )

    except HTTPException:
        raise  # re-raise HTTP exceptions as-is

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api.main:app", host="0.0.0.0", port=8000, reload=True)