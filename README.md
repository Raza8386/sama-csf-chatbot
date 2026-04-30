# SAMA CSF Compliance Chatbot

An AI-powered compliance assistant that answers questions about the **SAMA Cyber Security Framework** using Retrieval Augmented Generation (RAG). Answers are grounded directly in the official PDF — no hallucination.

---

## How it works

```
Your question
    ↓
ChromaDB retrieves the 5 most relevant PDF chunks
    ↓
GPT-4o reads those chunks + your question
    ↓
Structured compliance answer + source page references
```

---

## Prerequisites

| Requirement | Version | Notes |
|---|---|---|
| Python | 3.10 or higher | Check with `python --version` |
| OpenAI API key | Any tier | ~$0.01–0.05 per conversation |
| SAMA CSF PDF | Latest version | Free download from SAMA website |

---

## Step-by-step setup

### 1. Download the SAMA CSF PDF

1. Visit the Saudi Central Bank (SAMA) rules and instructions page:  
   **https://www.sama.gov.sa/en-US/RulesInstructions/**
2. Under the Cyber Security section, download the **SAMA Cyber Security Framework**
3. Rename the file to exactly: `sama_csf.pdf`
4. Place it inside the `sama_chatbot/` folder (the same folder as `app.py`)

> Alternatively, search Google for: **"SAMA Cyber Security Framework PDF site:sama.gov.sa"**

---

### 2. Get an OpenAI API key

1. Sign in or create an account at **https://platform.openai.com/**
2. Go to **API Keys** (top-right menu → "View API Keys")
3. Click **"Create new secret key"**
4. Copy the key — it starts with `sk-...`
5. Add a small credit balance (Settings → Billing → Add payment method)  
   *(The chatbot costs roughly $0.01–0.05 per session)*

---

### 3. Create your `.env` file

In the `sama_chatbot/` folder, create a file named `.env`:

**Windows (Command Prompt):**
```cmd
copy .env.example .env
```

**Mac / Linux:**
```bash
cp .env.example .env
```

Open `.env` with any text editor and replace `your-openai-api-key-here` with your real key:

```
OPENAI_API_KEY=sk-proj-abc123...
```

> ⚠️ Never share your `.env` file or commit it to Git.

---

### 4. Create a Python virtual environment (recommended)

```bash
# Navigate to the project folder
cd "sama_chatbot"

# Create a virtual environment
python -m venv venv

# Activate it
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate
```

---

### 5. Install dependencies

```bash
pip install -r requirements.txt
```

This installs LangChain, ChromaDB, Streamlit, and all other required packages.  
Expect 2–5 minutes on first install.

---

### 6. Index the SAMA CSF PDF (run once)

```bash
python index_docs.py
```

This script:
- Reads `sama_csf.pdf` page by page
- Splits it into ~1,000-character chunks
- Embeds each chunk using OpenAI (`text-embedding-3-small`)
- Saves everything to a local folder called `sama_db/`

**Expected output:**
```
============================================================
  SAMA CSF Document Indexer
============================================================
📄  Loading PDF: sama_csf.pdf
    ✔  Loaded 82 pages from PDF
    ✔  Split into 347 chunks (size=1000, overlap=150)
🔢  Creating embeddings with model: text-embedding-3-small
💾  Saving vector store to: ./sama_db
    ✔  Vector store saved at: ./sama_db
============================================================
  ✅  Indexing Complete!
============================================================
```

*You only need to run this once.* The `sama_db/` folder persists between sessions.

---

### 7. Launch the chatbot

```bash
streamlit run app.py
```

The app opens automatically in your browser at **http://localhost:8501**

---

## Example questions to test

Try these after the app loads:

- *"What are the maturity level 3 requirements for cybersecurity governance?"*
- *"What does SAMA CSF require for vulnerability management?"*
- *"How should third-party cybersecurity risk be managed?"*
- *"What are the incident response requirements?"*
- *"What controls are required for privileged access management?"*
- *"What does SAMA CSF say about security awareness training?"*
- *"What are the data classification requirements?"*
- *"How often should penetration testing be performed?"*

---

## Project structure

```
sama_chatbot/
├── app.py            ← Streamlit chatbot UI (main entry point)
├── index_docs.py     ← One-time PDF indexing script
├── config.py         ← All settings in one place
├── requirements.txt  ← Python dependencies
├── .env.example      ← Template for environment variables
├── .env              ← Your actual API key (not committed to Git)
├── sama_csf.pdf      ← SAMA CSF PDF (you add this)
└── sama_db/          ← ChromaDB vector index (auto-created by index_docs.py)
```

---

## Troubleshooting

### `❌ OPENAI_API_KEY is not set`
- Check that `.env` exists in the `sama_chatbot/` folder (not `.env.example`)
- Verify the key is on its own line: `OPENAI_API_KEY=sk-...`
- Make sure there are no spaces around the `=` sign

### `❌ PDF not found: sama_csf.pdf`
- Confirm the file is in the same folder as `index_docs.py`
- Confirm the filename is exactly `sama_csf.pdf` (lowercase, no spaces)

### `🔴 Knowledge base not loaded` in the app
- You haven't run `python index_docs.py` yet, or it failed
- Run `python index_docs.py` and wait for the "Indexing Complete" message
- Then restart the Streamlit app

### `ModuleNotFoundError: No module named 'langchain'`
- Your virtual environment is not activated, or dependencies weren't installed
- Run `pip install -r requirements.txt` again with the venv active

### App is slow on first load
- ChromaDB loads into memory on first query — this is normal (5–10 seconds)
- Subsequent queries are much faster

### OpenAI API error: `AuthenticationError`
- Your API key is invalid or has been revoked
- Generate a new key at https://platform.openai.com/api-keys

### OpenAI API error: `RateLimitError` or `InsufficientQuotaError`
- Add credit to your OpenAI account at https://platform.openai.com/settings/billing

---

## Configuration

All settings are in `config.py`. You can change:

| Setting | Default | Description |
|---|---|---|
| `EMBEDDING_MODEL` | `text-embedding-3-small` | OpenAI embedding model |
| `LLM_MODEL` | `gpt-4o` | OpenAI chat model |
| `CHUNK_SIZE` | `1000` | Characters per chunk |
| `CHUNK_OVERLAP` | `150` | Overlap between chunks |
| `TOP_K_RESULTS` | `5` | Chunks retrieved per query |

If you change `CHUNK_SIZE` or `CHUNK_OVERLAP`, re-run `python index_docs.py` to rebuild the index.

---

## Cost estimate

| Operation | Cost |
|---|---|
| Indexing (one-time, ~350 chunks) | ~$0.002 |
| Per question (retrieval + GPT-4o) | ~$0.01–0.05 |
| 100 questions/month | ~$1–5 |

---

*Built with LangChain · ChromaDB · OpenAI · Streamlit*
