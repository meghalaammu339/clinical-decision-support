from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, List
from core.graph import clinical_graph
from langchain.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from core.config import get_llm
import json
import json as json_lib
import requests as http_requests
from langgraph.types import Command
import uuid
import asyncio


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
    thread_id: Optional[str] = None
    current_step: Optional[str]
    structured_case: Optional[dict]
    differential_diagnosis: Optional[dict]
    final_report: Optional[dict]
    critique: Optional[str]
    error: Optional[str]
    confidence_score: Optional[int]
    risk_assessment: Optional[dict]
    guardrail_input_result: Optional[dict] = None
    guardrail_output_result: Optional[dict] = None
    output_safety_warning: Optional[list] = None


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


class ApprovalRequest(BaseModel):
    thread_id: str
    approved: bool
    doctor_notes: Optional[str] = None


@app.post("/analyze/stream")
async def analyze_stream(request: PatientCaseRequest):
    thread_id = f"case-{uuid.uuid4()}"
    initial_state = {
        "messages": [],
        "raw_input": request.model_dump(),
        "risk_assessment": None,
        "structured_case": None,
        "retrieved_evidence": None,
        "differential_diagnosis": None,
        "critique": None,
        "missed_diagnoses": None,
        "confidence_score": None,
        "final_report": None,
        "next_agent": None,
        "loop_count": 0,
        "error": None,
        "current_step": "starting",
        "guardrail_input_result": None,
        "guardrail_output_result": None,
        "output_safety_warning": None,
        "human_approved": False,
        "human_notes": None
    }
    config = {"configurable": {"thread_id": thread_id}}

    async def event_generator():
        yield f"data: {json_lib.dumps({'type': 'thread_id', 'thread_id': thread_id})}\n\n"
        # Track accumulated state so we can send a complete final event
        accumulated = {**initial_state}
        try:
            for chunk in clinical_graph.stream(initial_state, config=config, stream_mode="updates"):
                for node_name, node_output in chunk.items():
                    # Merge into accumulated state
                    accumulated = {**accumulated, **node_output}
                    event = {
                        "type": "node_complete",
                        "node": node_name,
                        "current_step": node_output.get("current_step"),
                        "data": {}
                    }
                    if node_name == "input_guardrail":
                        event["data"]["guardrail"] = node_output.get("guardrail_input_result")
                    elif node_name == "risk_agent":
                        event["data"]["risk_assessment"] = node_output.get("risk_assessment")
                    elif node_name == "intake_agent":
                        sc = node_output.get("structured_case") or {}
                        event["data"]["chief_complaint"] = sc.get("chief_complaint")
                        event["data"]["structured_case"] = node_output.get("structured_case")
                    elif node_name == "extract_evidence":
                        evidence = node_output.get("retrieved_evidence") or []
                        event["data"]["evidence_count"] = len(evidence)
                    elif node_name == "diagnosis_agent":
                        dx = node_output.get("differential_diagnosis") or {}
                        event["data"]["primary_diagnosis"] = dx.get("primary_diagnosis")
                        event["data"]["differential_diagnosis"] = node_output.get("differential_diagnosis")
                    elif node_name == "critique_agent":
                        event["data"]["confidence_score"] = node_output.get("confidence_score")
                        event["data"]["critique"] = node_output.get("critique")
                    elif node_name == "human_review":
                        if node_output.get("current_step") == "awaiting_human_approval":
                            event["type"] = "awaiting_approval"
                    elif node_name == "output_guardrail":
                        event["data"]["warnings"] = node_output.get("output_safety_warning")
                    yield f"data: {json_lib.dumps(event)}\n\n"
                    await asyncio.sleep(0)

            # Send complete final state so frontend has everything it needs
            final_event = {
                "type": "final",
                "data": {
                    "final_report": accumulated.get("final_report"),
                    "structured_case": accumulated.get("structured_case"),
                    "differential_diagnosis": accumulated.get("differential_diagnosis"),
                    "risk_assessment": accumulated.get("risk_assessment"),
                    "confidence_score": accumulated.get("confidence_score"),
                    "critique": accumulated.get("critique"),
                    "output_safety_warning": accumulated.get("output_safety_warning"),
                }
            }
            yield f"data: {json_lib.dumps(final_event)}\n\n"
            yield f"data: {json_lib.dumps({'type': 'done'})}\n\n"
        except Exception as e:
            yield f"data: {json_lib.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}
    )


@app.post("/analyze")
async def analyze_patient(request: PatientCaseRequest):
    thread_id = f"case-{uuid.uuid4()}"
    initial_state = {
        "messages": [],
        "raw_input": request.model_dump(),
        "risk_assessment": None,
        "structured_case": None,
        "retrieved_evidence": None,
        "differential_diagnosis": None,
        "critique": None,
        "missed_diagnoses": None,
        "confidence_score": None,
        "final_report": None,
        "next_agent": None,
        "loop_count": 0,
        "error": None,
        "current_step": "starting",
        "guardrail_input_result": None,
        "guardrail_output_result": None,
        "output_safety_warning": None,
        "human_approved": False,
        "human_notes": None
    }
    config = {"configurable": {"thread_id": thread_id}}

    try:
        result = clinical_graph.invoke(initial_state, config=config)

        if (result.get("error") or "").startswith("INPUT_BLOCKED"):
            raise HTTPException(status_code=400, detail=result["error"])

        # Graph paused at interrupt() — emergent case waiting for doctor
        if result.get("current_step") == "awaiting_human_approval":
            return {
                "status": "awaiting_approval",
                "thread_id": thread_id,
                "current_step": "awaiting_human_approval",
                "differential_diagnosis": result.get("differential_diagnosis"),
                "urgency": (result.get("final_report") or {}).get("urgency"),
                "message": "Emergent case detected. Doctor approval required before finalizing report."
            }

        if result.get("error"):
            raise HTTPException(status_code=500, detail=result["error"])

        return DiagnosisResponse(
            status="success",
            thread_id=thread_id,
            current_step=result.get("current_step"),
            structured_case=result.get("structured_case"),
            differential_diagnosis=result.get("differential_diagnosis"),
            final_report=result.get("final_report"),
            critique=result.get("critique"),
            confidence_score=result.get("confidence_score"),
            risk_assessment=result.get("risk_assessment"),
            guardrail_input_result=result.get("guardrail_input_result"),
            guardrail_output_result=result.get("guardrail_output_result"),
            output_safety_warning=result.get("output_safety_warning"),
            error=None
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/approve")
async def approve_case(request: ApprovalRequest):
    config = {"configurable": {"thread_id": request.thread_id}}
    try:
        result = clinical_graph.invoke(
            Command(resume={"approved": request.approved, "doctor_notes": request.doctor_notes}),
            config=config
        )

        if not request.approved:
            return {"status": "rejected", "message": "Case rejected by doctor. Pipeline terminated."}

        return DiagnosisResponse(
            status="success",
            thread_id=request.thread_id,
            current_step=result.get("current_step"),
            structured_case=result.get("structured_case"),
            differential_diagnosis=result.get("differential_diagnosis"),
            final_report=result.get("final_report"),
            critique=result.get("critique"),
            confidence_score=result.get("confidence_score"),
            risk_assessment=result.get("risk_assessment"),
            guardrail_input_result=result.get("guardrail_input_result"),
            guardrail_output_result=result.get("guardrail_output_result"),
            output_safety_warning=result.get("output_safety_warning"),
            error=None
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api.main:app", host="0.0.0.0", port=8000, reload=True)