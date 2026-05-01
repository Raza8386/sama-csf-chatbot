"""
config.py - Central configuration for the SAMA CSF Compliance Chatbot

All settings live here. Edit this file to change models, paths, or chunking behavior.
You should never need to touch app.py or index_docs.py to change these values.
"""

import os
from dotenv import load_dotenv

# Load the .env file so ANTHROPIC_API_KEY is available as an environment variable
load_dotenv()

# ── Anthropic credentials ───────────────────────────────────────────────────
# Check .env first (local), then Streamlit secrets (cloud deployment)
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

if not ANTHROPIC_API_KEY:
    try:
        import streamlit as st
        ANTHROPIC_API_KEY = st.secrets.get("ANTHROPIC_API_KEY")
    except Exception:
        pass

if not ANTHROPIC_API_KEY:
    raise EnvironmentError(
        "\n\n❌  ANTHROPIC_API_KEY is not set.\n"
        "Please create a .env file in the sama_chatbot/ folder with:\n\n"
        "    ANTHROPIC_API_KEY=sk-ant-...\n\n"
        "Get your key at: https://console.anthropic.com/settings/keys\n"
    )

# ── Model settings ──────────────────────────────────────────────────────────
# Embedding model — uses HuggingFace sentence-transformers (free, runs locally)
# Anthropic does not provide an embedding API, so we use a local model instead.
EMBEDDING_MODEL = "all-MiniLM-L6-v2"

# LLM used to generate the compliance answer (Anthropic Claude)
LLM_MODEL = "claude-haiku-4-5"

# ── Document chunking settings ──────────────────────────────────────────────
# Each PDF page is split into smaller overlapping chunks for better retrieval
CHUNK_SIZE = 1000        # Max characters per chunk
CHUNK_OVERLAP = 150      # Characters shared between adjacent chunks (preserves context at boundaries)

# ── Retrieval settings ──────────────────────────────────────────────────────
# How many chunks to fetch from ChromaDB per query (user can override in sidebar)
TOP_K_RESULTS = 5

# ── ChromaDB (local vector database) settings ───────────────────────────────
# ChromaDB stores vectors on disk — no cloud, no signup required
CHROMA_DB_PATH = "./sama_db"          # Folder where the vector index is saved
COLLECTION_NAME = "sama_csf"          # Name of the collection inside ChromaDB

# ── Source document path ────────────────────────────────────────────────────
# Place your SAMA CSF PDF in the sama_chatbot/ folder with this exact filename
PDF_PATH = "sama_csf.pdf"

# ── SAMA CSF Domain list ────────────────────────────────────────────────────
# Used in the sidebar filter — these match the official framework structure
SAMA_DOMAINS = [
    "Cybersecurity Leadership and Governance",
    "Cybersecurity Risk Management",
    "Cybersecurity Operations and Technology",
    "Third-Party Cybersecurity",
    "Cybersecurity Resilience",
    "Application Security",
    "Data and Cloud Security",
    "Industrial Systems Security",
]

# ── System prompt for the RAG chain ────────────────────────────────────────
# This instructs the LLM to behave as a SAMA CSF compliance expert.
# {context} and {question} are filled in automatically by LangChain.
SYSTEM_PROMPT = """You are an expert SAMA Cyber Security Framework (CSF) compliance advisor with deep experience in GRC, cybersecurity auditing, and Saudi Arabian financial sector regulations.

Answer the compliance question below using ONLY the provided SAMA CSF context sections. Structure your answer clearly with:
- The relevant SAMA CSF domain and control reference
- The specific requirement or control objective
- The maturity level expectations if mentioned
- Practical implementation guidance based on the framework

If the answer is not found in the provided context, respond with: "This specific requirement does not appear in the SAMA CSF sections retrieved. Try rephrasing your question or ask about a related control domain."

Context from SAMA CSF document:
{context}

Compliance question: {question}

Provide a structured, professional answer suitable for a cybersecurity auditor:"""
