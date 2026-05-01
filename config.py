"""
config.py - Central configuration for the GRC Compliance Chatbot

All settings live here. Edit this file to change models, paths, or chunking behavior.
You should never need to touch app.py or index_docs.py to change these values.
"""

import os
from dotenv import load_dotenv

# Load the .env file so ANTHROPIC_API_KEY is available as an environment variable
load_dotenv()

# ── Anthropic credentials ───────────────────────────────────────────────────
# Reads from .env file (local). On Streamlit Cloud, users enter their key
# in the sidebar — so None here is fine, app.py handles the missing key.
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

# ── Model settings ──────────────────────────────────────────────────────────
# Embedding model — uses HuggingFace sentence-transformers (free, runs locally)
EMBEDDING_MODEL = "all-MiniLM-L6-v2"

# LLM used to generate the compliance answer (Anthropic Claude)
LLM_MODEL = "claude-haiku-4-5"

# ── Document chunking settings ──────────────────────────────────────────────
CHUNK_SIZE = 1000        # Max characters per chunk
CHUNK_OVERLAP = 150      # Characters shared between adjacent chunks

# ── Retrieval settings ──────────────────────────────────────────────────────
TOP_K_RESULTS = 5

# ── ChromaDB (local vector database) settings ───────────────────────────────
CHROMA_DB_PATH = "./sama_db"
COLLECTION_NAME = "grc_frameworks"

# ── Multi-framework PDF sources ─────────────────────────────────────────────
# Add more frameworks here — key is the display name, value is the PDF filename.
# Place all PDFs in the sama_chatbot/ folder.
PDF_SOURCES = {
    "SAMA CSF": "sama_csf.pdf",
    "PDPL":     "pdpl.pdf",
    "NCA ECC":  "nca_ecc.pdf",
}

# ── Framework domains ────────────────────────────────────────────────────────
# Used in the sidebar domain filter, grouped by framework.
FRAMEWORK_DOMAINS = {
    "SAMA CSF": [
        "Cybersecurity Leadership and Governance",
        "Cybersecurity Risk Management",
        "Cybersecurity Operations and Technology",
        "Third-Party Cybersecurity",
        "Cybersecurity Resilience",
        "Application Security",
        "Data and Cloud Security",
        "Industrial Systems Security",
    ],
    "PDPL": [
        "Data Collection and Processing",
        "Personal Data Rights",
        "Consent and Legal Basis",
        "Data Retention and Destruction",
        "Cross-border Data Transfers",
        "Data Breach Notification",
        "Data Protection Officer",
        "Privacy Notice and Transparency",
    ],
    "NCA ECC": [
        "Cybersecurity Governance",
        "Cybersecurity Risk Management",
        "Cybersecurity Operations",
        "Third-Party and Cloud Security",
        "Industrial Control Systems Security",
        "Cybersecurity Resilience",
        "Physical Security",
        "Asset Management",
        "Identity and Access Management",
        "Information Protection",
    ],
}

# Flat list of all domains (used when no framework filter is selected)
SAMA_DOMAINS = [d for domains in FRAMEWORK_DOMAINS.values() for d in domains]

# ── System prompt for the RAG chain ────────────────────────────────────────
SYSTEM_PROMPT = """You are an expert GRC (Governance, Risk and Compliance) advisor specialising in Saudi Arabian regulations including the SAMA Cyber Security Framework (CSF), the Personal Data Protection Law (PDPL), and the NCA Essential Cybersecurity Controls (ECC). You have deep experience in cybersecurity auditing, data privacy compliance, and Saudi regulatory requirements.

Answer the compliance question below using ONLY the provided context sections from the relevant framework document. Structure your answer clearly with:
- The relevant framework name, domain, and control/article reference
- The specific requirement or obligation
- The maturity level or penalty implications if mentioned
- Practical implementation guidance based on the framework

If the answer is not found in the provided context, respond with: "This specific requirement does not appear in the retrieved sections. Try rephrasing your question or selecting a different framework."

Context from compliance framework document:
{context}

Compliance question: {question}

Provide a structured, professional answer suitable for a GRC auditor or compliance officer:"""
