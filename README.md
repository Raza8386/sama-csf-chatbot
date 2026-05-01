# 🛡️ SAMA CSF Compliance Assistant

An AI-powered compliance chatbot that answers questions about the **SAMA Cyber Security Framework (CSF)** using Retrieval Augmented Generation (RAG). Answers are grounded directly in the official SAMA CSF PDF — no hallucination, no guessing.

🌐 **Live Demo:** [sama-csf-chatbot.streamlit.app](https://sama-csf-chatbot-hx8aqfwx3appqe9qsh366x7.streamlit.app)

---

## 📸 Features

- ✅ **RAG-powered answers** grounded in the official SAMA CSF document
- ✅ **Claude AI** (Anthropic `claude-haiku-4-5`) for structured compliance responses
- ✅ **Local embeddings** via HuggingFace `all-MiniLM-L6-v2` — free, no API cost
- ✅ **ChromaDB** vector database for fast semantic search
- ✅ **Domain filter** — focus queries on specific SAMA CSF domains
- ✅ **Source pages** — see exactly which PDF pages backed each answer
- ✅ **Confidence indicator** — High / Medium / Low based on retrieved chunks
- ✅ **Streamlit UI** — clean, interactive chat interface
- ✅ **Publicly deployed** on Streamlit Community Cloud

---

## 🚀 Try it online

Visit the live app — no installation needed:

**👉 [https://sama-csf-chatbot-hx8aqfwx3appqe9qsh366x7.streamlit.app](https://sama-csf-chatbot-hx8aqfwx3appqe9qsh366x7.streamlit.app)**

1. Enter your **Anthropic API key** in the sidebar (get one free at [console.anthropic.com](https://console.anthropic.com/settings/keys))
2. Ask any SAMA CSF compliance question
3. Get a structured answer with source page references

---

## 🏗️ How it works

```
Your compliance question
        ↓
ChromaDB retrieves the 5 most relevant SAMA CSF chunks
        ↓
Claude (claude-haiku-4-5) reads those chunks + your question
        ↓
Structured compliance answer + source page references
```

---

## 🖥️ Run locally

### Prerequisites

| Requirement | Version | Notes |
|---|---|---|
| Python | 3.10 or higher | Check with `python --version` |
| Anthropic API key | Any tier | Free at [console.anthropic.com](https://console.anthropic.com/settings/keys) |
| SAMA CSF PDF | Latest version | Free download from SAMA website |

---

### Step 1 — Clone the repository

```bash
git clone https://github.com/Raza8386/sama-csf-chatbot.git
cd sama-csf-chatbot/sama_chatbot
```

---

### Step 2 — Download the SAMA CSF PDF

1. Visit: **https://www.sama.gov.sa/en-US/RulesInstructions/**
2. Search for **Cyber Security Framework** and download the PDF
3. Rename it to exactly: `sama_csf.pdf`
4. Place it in the `sama_chatbot/` folder

---

### Step 3 — Get an Anthropic API key

1. Go to **https://console.anthropic.com/settings/keys**
2. Click **Create key**
3. Copy the key — it starts with `sk-ant-...`

---

### Step 4 — Create your `.env` file

```bash
# Windows
copy .env.example .env

# Mac / Linux
cp .env.example .env
```

Open `.env` and add your key:

```
ANTHROPIC_API_KEY=sk-ant-...
```

> ⚠️ Never share your `.env` file or commit it to Git.

---

### Step 5 — Install dependencies

```bash
pip install -r requirements.txt
```

---

### Step 6 — Index the SAMA CSF PDF (run once)

```bash
python index_docs.py
```

This will:
- Load and split the PDF into chunks
- Download the `all-MiniLM-L6-v2` embedding model (~90 MB, one-time)
- Save the vector database to `sama_db/`

**Expected output:**
```
============================================================
  SAMA CSF Document Indexer
============================================================
📄  Loading PDF: sama_csf.pdf
    ✔  Loaded 56 pages from PDF
    ✔  Split into 171 chunks (size=1000, overlap=150)
🔢  Creating embeddings with model: all-MiniLM-L6-v2
💾  Saving vector store to: ./sama_db
    ✔  Vector store saved at: ./sama_db
============================================================
  ✅  Indexing Complete!
============================================================
```

---

### Step 7 — Launch the chatbot

```bash
python -m streamlit run app.py
```

Open your browser at **http://localhost:8501**

---

## 💬 Example questions

- *"What are the maturity level 3 requirements for cybersecurity governance?"*
- *"What does SAMA CSF require for vulnerability management?"*
- *"How should third-party cybersecurity risk be managed?"*
- *"What are the incident response requirements?"*
- *"What controls are required for privileged access management?"*
- *"What does SAMA CSF say about security awareness training?"*
- *"What are the data classification requirements?"*
- *"How often should penetration testing be performed?"*

---

## 📁 Project structure

```
sama_chatbot/
├── app.py              ← Streamlit chatbot UI (main entry point)
├── index_docs.py       ← One-time PDF indexing script
├── config.py           ← All settings in one place
├── requirements.txt    ← Python dependencies
├── .env.example        ← Template for environment variables
├── .env                ← Your actual API key (not committed to Git)
├── .streamlit/
│   └── config.toml     ← Streamlit server settings
├── sama_csf.pdf        ← SAMA CSF PDF
└── sama_db/            ← ChromaDB vector index (auto-created)
```

---

## ⚙️ Configuration

All settings are in `config.py`:

| Setting | Default | Description |
|---|---|---|
| `EMBEDDING_MODEL` | `all-MiniLM-L6-v2` | HuggingFace local embedding model |
| `LLM_MODEL` | `claude-haiku-4-5` | Anthropic Claude model |
| `CHUNK_SIZE` | `1000` | Characters per chunk |
| `CHUNK_OVERLAP` | `150` | Overlap between adjacent chunks |
| `TOP_K_RESULTS` | `5` | Chunks retrieved per query |

> If you change `CHUNK_SIZE` or `CHUNK_OVERLAP`, re-run `python index_docs.py` to rebuild the index.

---

## 🔍 SAMA CSF Domains covered

- Cybersecurity Leadership and Governance
- Cybersecurity Risk Management
- Cybersecurity Operations and Technology
- Third-Party Cybersecurity
- Cybersecurity Resilience
- Application Security
- Data and Cloud Security
- Industrial Systems Security

---

## 🛠️ Troubleshooting

### `❌ ANTHROPIC_API_KEY is not set`
- Check that `.env` exists in the `sama_chatbot/` folder
- Verify the key is on its own line: `ANTHROPIC_API_KEY=sk-ant-...`
- No spaces around the `=` sign

### `❌ PDF not found: sama_csf.pdf`
- Confirm the file is in the same folder as `index_docs.py`
- Filename must be exactly `sama_csf.pdf` (lowercase, no spaces)

### `🔴 Knowledge base not loaded`
- Run `python index_docs.py` first and wait for "Indexing Complete"
- Then restart the Streamlit app

### `ModuleNotFoundError`
- Run `pip install -r requirements.txt` again
- Make sure your virtual environment is activated

### `invalid x-api-key` error
- Your Anthropic API key is invalid or expired
- Create a new key at [console.anthropic.com/settings/keys](https://console.anthropic.com/settings/keys)

---

## 💰 Cost estimate

| Operation | Cost |
|---|---|
| Indexing (one-time, 171 chunks) | **Free** — local embeddings |
| Per question (Claude Haiku) | ~$0.001–0.005 |
| 100 questions/month | ~$0.10–0.50 |

> Embeddings are completely free — they run locally on your machine using HuggingFace sentence-transformers.

---

## 🧰 Tech stack

| Component | Technology |
|---|---|
| LLM | Anthropic Claude (`claude-haiku-4-5`) |
| Embeddings | HuggingFace `all-MiniLM-L6-v2` (local, free) |
| Vector DB | ChromaDB (local) |
| RAG Framework | LangChain |
| UI | Streamlit |
| Deployment | Streamlit Community Cloud |

---

## 👤 Author

**Danish Raza** — GRC Professional  
📧 danishraza786@gmail.com  
🔗 [github.com/Raza8386](https://github.com/Raza8386)

---

*Built with LangChain · ChromaDB · Anthropic Claude · HuggingFace · Streamlit*
