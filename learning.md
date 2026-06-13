
state.py 

— The Shared State
This is the most important concept in LangGraph.

Think of ClinicalState as a shared whiteboard that gets passed to every agent. Each agent reads from it and writes their output back to it. No agent talks to another directly — they only read/write this state.

Intake Agent → writes structured_case to state
RAG Agent    → reads structured_case, writes retrieved_evidence
Diagnosis    → reads both, writes differential_diagnosis  
Critique     → reads everything, writes final_report
TypedDict is just a Python dict with type hints — LangGraph requires this so it knows the shape of your state.



core/config.py

 — this is where you initialize the LLM (Groq) and embeddings (HuggingFace). These are used by multiple agents so we define them once here and import wherever needed.


 core/vectorstore.py
 
 — this is the RAG knowledge base.
What happens here:
We define medical knowledge as a list of text chunks
Convert them to embeddings using HuggingFace
Store in FAISS so we can do similarity search later
If index already exists on disk, just load it — don't rebuild every time



intake_agent.py 


— First Agent in the Pipeline
What this agent does:
Takes the messy free-text patient input and converts it into a clean structured JSON. Every agent after this reads from that structured output — so this agent is critical. Garbage in = garbage out for the whole pipeline.
How it works:
Raw patient input (symptoms, age, etc.)
        ↓
LangChain LCEL chain = prompt | llm | output parser
        ↓
Clean structured JSON written to state
What is LCEL? — It's LangChain's pipe syntax. prompt | llm | parser means: feed prompt to llm, feed llm output to parser. That's it.


rag_agent.py —

 Second Agent, The Decision Maker
What this agent does:
Takes the search_keywords extracted by intake agent, searches FAISS first, checks the score, decides whether to use FAISS result or call PubMed live.
search_keywords from state
        ↓
search FAISS → get docs + best_score
        ↓
score < 1.0?  → use FAISS docs
score >= 1.0? → call PubMed live with keywords → use those docs
        ↓
write retrieved_evidence to state


diagnosis_agent.py 

— Third Agent, The Diagnostician
What this agent does:

Takes the structured patient case + retrieved evidence and generates a ranked differential diagnosis. This is the core clinical reasoning step.

structured_case + retrieved_evidence from state
        ↓
Build prompt with both
        ↓
LLM reasons over patient data + evidence
        ↓
Returns ranked list of possible diagnoses with supporting/against evidence
        ↓
Write differential_diagnosis to state



critique_agent.py


 — Final Agent, The Validator
What this agent does:
Acts as a senior doctor reviewing the diagnosis. It challenges the reasoning, checks for missed conditions, validates urgency levels, and produces the final consolidated report.
structured_case + retrieved_evidence + differential_diagnosis from state
        ↓
LLM critically reviews everything
        ↓
Flags missed diagnoses, blind spots, concerns
        ↓
Produces final_report — the clean output the frontend displays
        ↓
Writes critique + final_report to state
This agent is what makes the system feel like a multi-agent pipeline and not just one LLM call — it's a second opinion layer.


core/graph.py 

— The LangGraph Pipeline
What this file does:
This is where all 4 agents get connected into a pipeline. LangGraph uses a StateGraph — think of it as a flowchart where each node is an agent and edges define what runs next.
START
  ↓
intake → rag → diagnosis → critique
  ↓         ↓         ↓          ↓
error?    error?    error?      END
  ↓         ↓         ↓
 END       END       END
Conditional edges — after each agent, we check if there's an error in state. If yes, stop the pipeline. If no, continue to next agent. This prevents cascading failures.




api/main.py 

— FastAPI LayerWhat this file does:Exposes the LangGraph pipeline as a REST API endpoint. React frontend calls this. One endpoint — /analyze — takes patient data, runs it through the pipeline, returns the result.React sends POST /analyze with patient data
        ↓
FastAPI validates input with Pydantic
        ↓
Builds initial state
        ↓
Calls clinical_graph.invoke(initial_state)
        ↓
Returns final state as JSON response