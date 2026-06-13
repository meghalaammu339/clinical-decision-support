from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from core.graph import clinical_graph


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


@app.get("/health")
def health_check():
    # Simple endpoint to check if API is running
    return {"status": "healthy"}


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
            critique=result.get("critique"),
            error=None
        )

    except HTTPException:
        raise  # re-raise HTTP exceptions as-is

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api.main:app", host="0.0.0.0", port=8000, reload=True)