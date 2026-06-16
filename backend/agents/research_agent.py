# from core.state import ClinicalState
# from core.vectorstore import search_faiss, fetch_from_pubmed

# SIMILARITY_THRESHOLD = 1.0


# def rag_agent(state: ClinicalState) -> ClinicalState:

#     if state.get("error"):
#         return state

#     structured = state["structured_case"]

#     keywords = structured.get("search_keywords", [])

#     # Only use keywords — short medical terms work best for PubMed
#     query = " ".join(keywords)
#     print(f"RAG agent searching for: {query}")

#     try:
#         faiss_docs, best_score = search_faiss(query, k=3)
#         print(f"FAISS best score: {best_score}")

#         if best_score < SIMILARITY_THRESHOLD and faiss_docs:
#             print("Using FAISS results")
#             evidence = faiss_docs
#             source_used = "faiss"

#         else:
#             print("FAISS score too high — falling through to PubMed")
#             pubmed_docs = fetch_from_pubmed(query, max_results=4)

#             if pubmed_docs:
#                 evidence = pubmed_docs
#                 source_used = "pubmed"
#             else:
#                 print("PubMed also failed — using FAISS as fallback")
#                 evidence = faiss_docs
#                 source_used = "faiss_fallback"

#         print(f"Evidence source: {source_used}, docs retrieved: {len(evidence)}")

#         return {
#             **state,
#             "retrieved_evidence": evidence,
#             "current_step": "rag_complete"
#         }

#     except Exception as e:
#         return {
#             **state,
#             "error": f"RAG agent failed: {str(e)}",
#             "current_step": "error"
#         }


from langchain_core.messages import SystemMessage, HumanMessage, ToolMessage
from langgraph.prebuilt import ToolNode
from core.config import get_llm
from core.state import ClinicalState
from core.tools import RESEARCH_TOOLS

llm_with_tools = get_llm().bind_tools(RESEARCH_TOOLS)

RESEARCH_SYSTEM_PROMPT = """You are a medical research agent.
Given a structured patient case, find relevant medical evidence.

Strategy:
1. Call search_medical_knowledge_base first with short keywords from the case.
2. If the returned score is above 1.0 or results look irrelevant, call search_pubmed_live with refined keywords.
3. Once you have enough evidence (usually 1-2 tool calls), stop calling tools and reply with a short plain-text summary of what you found.

Use short medical keyword queries, never full sentences."""


def research_agent(state: ClinicalState) -> ClinicalState:
    if state.get("error"):
        return state

    messages = state.get("messages", [])

    if not any(isinstance(m, SystemMessage) for m in messages):
        messages = [
            SystemMessage(content=RESEARCH_SYSTEM_PROMPT),
            HumanMessage(content=f"Structured case: {state['structured_case']}")
        ]

    response = llm_with_tools.invoke(messages)
    return {**state, "messages": messages + [response]}


research_tool_node = ToolNode(RESEARCH_TOOLS)


def extract_evidence_from_messages(state: ClinicalState) -> ClinicalState:
    evidence = [
        {"content": m.content, "source": m.name}
        for m in state["messages"] if isinstance(m, ToolMessage)
    ]
    return {**state, "retrieved_evidence": evidence, "current_step": "research_complete"}