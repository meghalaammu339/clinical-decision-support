from langchain_groq import ChatGroq
from langchain_huggingface import HuggingFaceEmbeddings
from dotenv import load_dotenv
import os

load_dotenv()  # reads your .env file and loads GROQ_API_KEY into environment

def get_llm():
    return ChatGroq(
        model="llama-3.3-70b-versatile",  # best free model on Groq
        temperature=0.3,  # low temp = more deterministic, good for clinical stuff
        api_key=os.getenv("GROQ_API_KEY")
    )

def get_embeddings():
    return HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
        # small, fast, runs locally, no API key needed
    )