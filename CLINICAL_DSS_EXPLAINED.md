# Clinical Decision Support Agent — Full Explanation

## What We Built

A **multi-agent AI system** that takes a patient case (symptoms, age, history, medications) and produces a differential diagnosis with evidence from medical literature.

**Resume line:**
> Multi-agent LangGraph pipeline for clinical decision support. Intake agent structures patient data via LangChain LCEL, RAG agent retrieves evidence from FAISS/PubMed with dynamic fallback, diagnosis agent generates ranked differentials with citations, critique agent validates reasoning. Stack: LangGraph, LangChain, Groq (Llama 3.3 70B), FAISS, FastAPI, React.

---

## Architecture Overview

```
User Input (symptoms, age, history, medications)
        │
        ▼
┌─────────────────┐
│  Intake Agent   │  ← LangChain LCEL chain
│                 │    Converts messy text → clean structured JSON
│  LCEL Chain:    │    Extracts: symptoms, red_flags, search_keywords
│  prompt|llm|    │
│  JsonParser     │
└────────┬────────┘
         │ structured_case written to state
         ▼
┌─────────────────┐
│   RAG Agent     │  ← Hybrid retrieval (FAISS + PubMed)
│                 │    Takes search_keywords from intake agent
│  FAISS search   │    If score < 1.0 → use FAISS (fast, 12 conditions)
│  + PubMed API   │    If score ≥ 1.0 → call PubMed live (any condition)
│  fallback       │
└────────┬────────┘
         │ retrieved_evidence written to state
         ▼
┌─────────────────┐
│ Diagnosis Agent │  ← LangChain LCEL chain
│                 │    Reads structured_case + retrieved_evidence
│  Generates      │    Produces ranked differential diagnoses
│  differential   │    With supporting/against evidence + urgency
│  diagnosis      │
└────────┬────────┘
         │ differential_diagnosis written to state
         ▼
┌─────────────────┐
│ Critique Agent  │  ← LangChain LCEL chain
│                 │    Acts as senior doctor reviewing the diagnosis
│  Validates      │    Checks for missed conditions, blind spots
│  reasoning,     │    Produces final consolidated report
│  final report   │
└────────┬────────┘
         │ final_report written to state
         ▼
     Final JSON Response (FastAPI → React)
```

---

## Core Concept: LangGraph State

**The most important thing to understand.**

All 4 agents share one object called `ClinicalState`. Think of it as a shared whiteboard passed from agent to agent. Each agent reads what it needs and writes its output back.

```python
class ClinicalState(TypedDict):
    raw_input: PatientCase           # user input — never changes
    structured_case: Optional[dict]  # intake agent writes this
    retrieved_evidence: Optional[List[dict]]  # rag agent writes this
    differential_diagnosis: Optional[dict]    # diagnosis agent writes this
    critique: Optional[str]          # critique agent writes this
    final_report: Optional[dict]     # critique agent writes this
    error: Optional[str]             # any agent can write this to stop pipeline
    current_step: Optional[str]      # tracks where we are
```

Every agent function follows this pattern:
```python
def some_agent(state: ClinicalState) -> ClinicalState:
    # read from state
    data = state["structured_case"]
    
    # do something
    result = process(data)
    
    # return updated state — spread operator keeps existing fields
    return {**state, "new_field": result, "current_step": "done"}
```

`{**state, "new_field": value}` — this copies everything already in state and adds/overwrites specific fields. This is the LangGraph pattern.

---

## File by File Explanation

### `core/state.py`
Defines `ClinicalState` — the shared data contract. No logic here, just the shape of the data. LangGraph requires a `TypedDict` so it knows what fields the state has.

### `core/config.py`
Initializes LLM (Groq) and embeddings (HuggingFace). Defined as functions (not variables) so they're lazy — only created when called, not on import.

```python
def get_llm():
    return ChatGroq(model="llama-3.3-70b-versatile", temperature=0.3)

def get_embeddings():
    return HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
```

### `core/vectorstore.py`
Two responsibilities:

**1. FAISS knowledge base (12 hardcoded conditions)**
Built once on first run, saved to disk. Loaded from disk on subsequent runs — no rebuild.

**2. Hybrid search logic**
```python
def search_faiss(query, k=3):
    # returns docs + best_score (L2 distance)
    # lower score = more similar

def fetch_from_pubmed(query, max_results=4):
    # Step 1: POST to PubMed esearch API → get matching IDs
    # Step 2: POST to PubMed efetch API → get abstract text
    # Returns list of abstract dicts
```

**Why L2 distance threshold of 1.0?**
FAISS uses L2 (Euclidean) distance between embedding vectors.
- Score < 1.0 = vectors are close = good semantic match → use FAISS
- Score ≥ 1.0 = vectors are far = poor match → condition not in our 12 → call PubMed

### `agents/intake_agent.py`
First agent. Uses LangChain LCEL:

```python
chain = INTAKE_PROMPT | llm | JsonOutputParser()
```

This is the pipe syntax:
- `INTAKE_PROMPT` formats the patient data into a prompt
- `llm` sends it to Groq and gets text back
- `JsonOutputParser` converts that text into a Python dict

The prompt instructs the LLM to return ONLY valid JSON — no extra text, no "Here is the JSON:" prefix, otherwise the parser breaks.

**Key output: `search_keywords`** — 3-5 medical terms extracted from symptoms. These drive the RAG search downstream.

### `agents/rag_agent.py`
Second agent. The decision maker:

```python
faiss_docs, best_score = search_faiss(query, k=3)

if best_score < 1.0 and faiss_docs:
    evidence = faiss_docs          # common condition → fast
else:
    pubmed_docs = fetch_from_pubmed(query)
    if pubmed_docs:
        evidence = pubmed_docs     # rare condition → accurate
    else:
        evidence = faiss_docs      # PubMed failed → graceful fallback
```

Three outcomes, always returns something — never crashes.

The search query is built from:
```python
query = f"{chief_complaint} {' '.join(keywords)}"
```
This is the patient's actual data — fully dynamic, not hardcoded.

### `agents/diagnosis_agent.py`
Third agent. Receives structured_case + retrieved_evidence, generates ranked differentials.

Key prompt rules:
- Rank up to 4 differentials
- Only cite sources from the evidence provided (reduces hallucination)
- Assign urgency: emergent / urgent / routine
- List supporting AND against evidence for each condition

### `agents/critique_agent.py`
Final agent. Acts as a second independent LLM pass — senior doctor reviewing the diagnosis.

Checks:
- Any missed conditions?
- Red flags properly addressed?
- Urgency levels appropriate?
- Any dangerous assumptions?

Produces `final_report` — the clean structured output the frontend displays.

**Why a critique agent?** Two LLM passes over the same problem catches more issues than one. The critique agent doesn't know what the diagnosis agent "intended" — it just sees the output and challenges it independently.

### `core/graph.py`
Wires all 4 agents into a LangGraph StateGraph:

```python
graph = StateGraph(ClinicalState)

graph.add_node("node_intake", intake_agent)
graph.add_node("node_rag", rag_agent)
graph.add_node("node_diagnosis", diagnosis_agent)
graph.add_node("node_critique", critique_agent)

graph.set_entry_point("node_intake")

# After each agent — check for error, stop if found
graph.add_conditional_edges("node_intake", should_continue, 
    {"continue": "node_rag", "end": END})
graph.add_conditional_edges("node_rag", should_continue, 
    {"continue": "node_diagnosis", "end": END})
graph.add_conditional_edges("node_diagnosis", should_continue, 
    {"continue": "node_critique", "end": END})

graph.add_edge("node_critique", END)

clinical_graph = graph.compile()
```

**Note:** Node names must not match state keys. We had a bug where `"critique"` was both a state key and a node name — LangGraph threw an error. Fixed by prefixing all node names with `"node_"`.

**`should_continue` router:**
```python
def should_continue(state: ClinicalState) -> str:
    if state.get("error"):
        return "end"   # stop pipeline
    return "continue"  # next agent
```

**`graph.compile()`** validates the graph structure and returns a runnable object with `.invoke()`.

### `api/main.py`
FastAPI layer. One endpoint `/analyze`:

1. Receives patient data, validates with Pydantic
2. Builds initial state (all fields None except raw_input)
3. Calls `clinical_graph.invoke(initial_state)`
4. Returns final state as JSON

CORS middleware allows React (port 5173) to call the API (port 8000).

---

## The Hybrid RAG Strategy (Your Idea)

This is the most interesting engineering decision in the project:

| Scenario | What Happens |
|----------|-------------|
| User describes chest pain | FAISS finds Myocardial Infarction, score 0.3 → use FAISS |
| User describes lupus symptoms | FAISS best match is UTI, score 1.8 → call PubMed live |
| PubMed API times out | Fall back to FAISS result anyway |

**Why this is impressive for interviews:**
- Shows you thought about edge cases (what if condition isn't in KB?)
- Shows graceful degradation (fallback when external API fails)
- Shows cost/performance tradeoff thinking (fast path vs accurate path)

---

## What Happens When You Run It

```
1. python -m api.main starts FastAPI + builds FAISS index from 12 conditions
2. POST /analyze receives patient data
3. clinical_graph.invoke(initial_state) runs:
   - intake_agent → structures the messy input
   - rag_agent → decides FAISS or PubMed, retrieves evidence
   - diagnosis_agent → generates differential with citations
   - critique_agent → validates, produces final report
4. Returns full JSON with all intermediate outputs + final report
```

---

## Tech Stack Summary

| Component | Technology | Why |
|-----------|-----------|-----|
| Agent Orchestration | LangGraph StateGraph | Explicit state, conditional edges, easy debugging |
| LLM Chains | LangChain LCEL | Clean pipe syntax, composable |
| LLM | Groq Llama 3.3 70B | Fast, free, high quality |
| Vector Store | FAISS | No C++ issues on Windows unlike ChromaDB |
| Embeddings | HuggingFace all-MiniLM-L6-v2 | Free, runs locally, no API key |
| Medical Literature | PubMed API | Free, real medical papers, no auth needed |
| Backend | FastAPI | Fast, auto docs, Pydantic validation |
| Frontend | React + Vite | (Tomorrow) |

---

## Tomorrow — Frontend

We'll build the React UI with:
- Patient intake form
- Pipeline visualization (shows which agent is running)
- Results display with urgency badges, differential cards, evidence citations
- Everything wired to the FastAPI backend

