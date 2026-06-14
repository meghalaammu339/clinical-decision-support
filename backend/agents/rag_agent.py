from core.state import ClinicalState
from core.vectorstore import search_faiss, fetch_from_pubmed

SIMILARITY_THRESHOLD = 1.0


def rag_agent(state: ClinicalState) -> ClinicalState:

    if state.get("error"):
        return state

    structured = state["structured_case"]

    keywords = structured.get("search_keywords", [])

    # Only use keywords — short medical terms work best for PubMed
    query = " ".join(keywords)
    print(f"RAG agent searching for: {query}")

    try:
        faiss_docs, best_score = search_faiss(query, k=3)
        print(f"FAISS best score: {best_score}")

        if best_score < SIMILARITY_THRESHOLD and faiss_docs:
            print("Using FAISS results")
            evidence = faiss_docs
            source_used = "faiss"

        else:
            print("FAISS score too high — falling through to PubMed")
            pubmed_docs = fetch_from_pubmed(query, max_results=4)

            if pubmed_docs:
                evidence = pubmed_docs
                source_used = "pubmed"
            else:
                print("PubMed also failed — using FAISS as fallback")
                evidence = faiss_docs
                source_used = "faiss_fallback"

        print(f"Evidence source: {source_used}, docs retrieved: {len(evidence)}")

        return {
            **state,
            "retrieved_evidence": evidence,
            "current_step": "rag_complete"
        }

    except Exception as e:
        return {
            **state,
            "error": f"RAG agent failed: {str(e)}",
            "current_step": "error"
        }