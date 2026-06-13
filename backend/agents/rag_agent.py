from core.state import ClinicalState
from core.vectorstore import search_faiss, fetch_from_pubmed

SIMILARITY_THRESHOLD = 1.0
# Lower score = more similar in FAISS (L2 distance)
# If best score is below threshold → FAISS result is relevant → use it
# If best score is above threshold → poor match → go to PubMed


def rag_agent(state: ClinicalState) -> ClinicalState:

    # Stop immediately if previous agent errored
    if state.get("error"):
        return state

    structured = state["structured_case"]

    # Get search keywords that intake agent extracted from patient input
    keywords = structured.get("search_keywords", [])
    chief_complaint = structured.get("chief_complaint", "")

    # Build search query from keywords + chief complaint
    # This is the actual patient-driven query — fully dynamic
    query = f"{chief_complaint} {' '.join(keywords)}"
    print(f"RAG agent searching for: {query}")

    try:
        # Step 1 — search FAISS first
        faiss_docs, best_score = search_faiss(query, k=3)
        print(f"FAISS best score: {best_score}")

        if best_score < SIMILARITY_THRESHOLD and faiss_docs:
            # Good match in our 12 conditions — use FAISS
            print("Using FAISS results")
            evidence = faiss_docs
            source_used = "faiss"

        else:
            # Poor match — condition likely outside our 12
            # Fall through to PubMed live search
            print("FAISS score too high — falling through to PubMed")
            pubmed_docs = fetch_from_pubmed(query, max_results=4)

            if pubmed_docs:
                evidence = pubmed_docs
                source_used = "pubmed"
            else:
                # PubMed also failed — use whatever FAISS had as fallback
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