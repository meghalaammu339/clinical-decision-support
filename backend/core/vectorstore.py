from langchain_community.vectorstores import FAISS
from langchain.schema import Document
from core.config import get_embeddings
import os
import requests

FAISS_PATH = "./faiss_index"

# 12 hardcoded conditions — fast lookup for common cases
MEDICAL_KNOWLEDGE = [
    {
        "content": "Chest pain with radiation to left arm, diaphoresis, and shortness of breath are classic symptoms of acute myocardial infarction. Immediate ECG and troponin levels are indicated. Risk factors include hypertension, diabetes, smoking, and hyperlipidemia.",
        "source": "Cardiology Guidelines 2024",
        "condition": "Myocardial Infarction"
    },
    {
        "content": "Sudden severe headache described as worst headache of life, neck stiffness, and photophobia are hallmark signs of subarachnoid hemorrhage. CT scan without contrast is first-line imaging.",
        "source": "Neurology Emergency Handbook",
        "condition": "Subarachnoid Hemorrhage"
    },
    {
        "content": "Fever, productive cough, pleuritic chest pain, and consolidation on chest X-ray indicate community-acquired pneumonia. Common pathogens include Streptococcus pneumoniae. Treatment with amoxicillin or macrolides.",
        "source": "Respiratory Medicine Guidelines",
        "condition": "Community-Acquired Pneumonia"
    },
    {
        "content": "Polyuria, polydipsia, polyphagia, and unexplained weight loss are hallmark symptoms of diabetes mellitus. Fasting glucose above 126 mg/dL or HbA1c above 6.5% confirms diagnosis.",
        "source": "ADA Diabetes Standards 2024",
        "condition": "Diabetes Mellitus"
    },
    {
        "content": "Unilateral leg swelling, pain, warmth, and erythema suggest deep vein thrombosis. D-dimer and Doppler ultrasound are primary diagnostic tools. Anticoagulation is first-line treatment.",
        "source": "Hematology Clinical Practice",
        "condition": "Deep Vein Thrombosis"
    },
    {
        "content": "Acute onset unilateral facial droop, arm weakness, speech difficulty are FAST symptoms of ischemic stroke. tPA within 4.5 hours of symptom onset. CT scan to rule out hemorrhage before thrombolysis.",
        "source": "Stroke Neurology Protocol",
        "condition": "Ischemic Stroke"
    },
    {
        "content": "Epigastric pain relieved by food or antacids, nausea, bloating, and dark stools suggest peptic ulcer disease. H. pylori infection is primary cause. Treatment: PPI therapy plus H. pylori eradication.",
        "source": "Gastroenterology Clinical Guide",
        "condition": "Peptic Ulcer Disease"
    },
    {
        "content": "Wheezing, shortness of breath, chest tightness, and cough especially at night are classic asthma symptoms. Spirometry confirms reversible airflow obstruction. Treatment: short-acting beta-agonists and inhaled corticosteroids.",
        "source": "GINA Asthma Guidelines 2024",
        "condition": "Asthma"
    },
    {
        "content": "Right lower quadrant pain at McBurney point, fever, nausea, anorexia, and elevated WBC suggest appendicitis. CT abdomen is gold standard. Surgical appendectomy is definitive treatment.",
        "source": "General Surgery Handbook",
        "condition": "Appendicitis"
    },
    {
        "content": "Fatigue, pallor, dyspnea on exertion, and low hemoglobin indicate anemia. Iron deficiency presents with low MCV and low ferritin. B12 deficiency causes macrocytic anemia.",
        "source": "Hematology Fundamentals",
        "condition": "Anemia"
    },
    {
        "content": "Dysuria, frequency, urgency, and suprapubic pain indicate urinary tract infection. Urine dipstick shows nitrites and leukocyte esterase. Common pathogen is E. coli. Treated with nitrofurantoin.",
        "source": "Infectious Disease Guidelines",
        "condition": "Urinary Tract Infection"
    },
    {
        "content": "Painless jaundice, dark urine, pale stools, and weight loss in older patient raise concern for pancreatic cancer or biliary obstruction. CA 19-9 may be elevated. ERCP or MRCP for biliary imaging.",
        "source": "Oncology Clinical Guidelines",
        "condition": "Pancreatic Malignancy"
    },
]

SIMILARITY_THRESHOLD = 1.0
# FAISS uses L2 distance — lower = more similar
# Below 1.0 means good match → use FAISS
# Above 1.0 means poor match → fall through to PubMed


def get_or_create_vectorstore():
    embeddings = get_embeddings()

    if os.path.exists(FAISS_PATH):
        return FAISS.load_local(
            FAISS_PATH,
            embeddings,
            allow_dangerous_deserialization=True
        )

    # First run — build from hardcoded knowledge
    docs = [
        Document(
            page_content=item["content"],
            metadata={"source": item["source"], "condition": item["condition"]}
        )
        for item in MEDICAL_KNOWLEDGE
    ]

    vectorstore = FAISS.from_documents(docs, embeddings)
    vectorstore.save_local(FAISS_PATH)
    return vectorstore


def search_faiss(query: str, k: int = 3):
    """
    Search FAISS with similarity scores.
    Returns (docs, best_score).
    best_score is the lowest distance found — we use this to decide
    whether to trust FAISS or fall through to PubMed.
    """
    vectorstore = get_or_create_vectorstore()
    results = vectorstore.similarity_search_with_score(query, k=k)
    # results = [(Document, score), (Document, score), ...]

    if not results:
        return [], 999  # no results → force PubMed

    best_score = min(score for _, score in results)
    docs = [
        {
            "content": doc.page_content,
            "source": doc.metadata.get("source"),
            "condition": doc.metadata.get("condition"),
            "score": round(score, 3)
        }
        for doc, score in results
    ]

    return docs, best_score


def fetch_from_pubmed(query: str, max_results: int = 4) -> list:
    """
    Called only when FAISS score is above threshold.
    Uses the patient's actual symptoms as the search query.
    So it's fully dynamic — works for any condition.
    """
    print(f"PubMed live fetch for: {query}")

    try:
        # Step 1 — get matching PubMed IDs
        search_resp = requests.get(
            "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi",
            params={
                "db": "pubmed",
                "term": query,
                "retmax": max_results,
                "retmode": "json",
                "sort": "relevance"
            },
            timeout=10
        )
        ids = search_resp.json()["esearchresult"]["idlist"]

        if not ids:
            return []

        # Step 2 — fetch abstract text using those IDs
        fetch_resp = requests.get(
            "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi",
            params={
                "db": "pubmed",
                "id": ",".join(ids),
                "rettype": "abstract",
                "retmode": "text"
            },
            timeout=10
        )

        raw_text = fetch_resp.text

        # abstracts are separated by blank lines in PubMed text response
        abstracts = [
            a.strip() for a in raw_text.split("\n\n")
            if len(a.strip()) > 100
        ]

        return [
            {
                "content": abstract[:1000],
                "source": "PubMed Live",
                "condition": "Retrieved from PubMed"
            }
            for abstract in abstracts[:max_results]
        ]

    except Exception as e:
        print(f"PubMed fetch failed: {e}")
        return []   