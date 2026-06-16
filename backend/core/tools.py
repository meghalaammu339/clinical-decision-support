from langchain_core.tools import tool
from core.vectorstore import search_faiss, fetch_from_pubmed


@tool
def search_medical_knowledge_base(query: str) -> str:
    """Search the internal FAISS knowledge base (12 common conditions) for medical evidence.
    Use short medical keywords, not full sentences. Score < 1.0 means a good match."""
    docs, score = search_faiss(query, k=3)
    if not docs:
        return "No results in internal knowledge base."
    formatted = "\n\n".join(
        f"[{d['condition']}] (score={d['score']}, source={d['source']}): {d['content']}"
        for d in docs
    )
    return f"Best match score: {score} (lower is better)\n\n{formatted}"


@tool
def search_pubmed_live(query: str) -> str:
    """Search PubMed live for conditions not covered by the internal knowledge base.
    Use short medical keywords, not full sentences."""
    docs = fetch_from_pubmed(query, max_results=4)
    if not docs:
        return "No PubMed results, try different keywords."
    return "\n\n".join(f"[{d['condition']}]: {d['content']}" for d in docs)


RESEARCH_TOOLS = [search_medical_knowledge_base, search_pubmed_live]