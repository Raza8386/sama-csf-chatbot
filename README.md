# 🛡️ GRC Compliance Assistant

An AI-powered compliance chatbot that answers questions about **SAMA Cyber Security Framework (CSF)**, **Personal Data Protection Law (PDPL)**, and **NCA Essential Cybersecurity Controls (ECC)** using Retrieval Augmented Generation (RAG). Answers are grounded directly in the official framework PDFs — no hallucination, no guessing.

🌐 **Live Demo:** [sama-csf-chatbot.streamlit.app](https://sama-csf-chatbot-hx8aqfwx3appqe9qsh366x7.streamlit.app)

---

## 📸 Features

- ✅ **Multi-framework support** — SAMA CSF, PDPL, and NCA ECC in one app
- ✅ **RAG-powered answers** grounded in official compliance documents
- ✅ **Claude AI** (Anthropic `claude-haiku-4-5`) for structured compliance responses
- ✅ **Local embeddings** via HuggingFace `all-MiniLM-L6-v2` — free, no API cost
- ✅ **ChromaDB** vector database for fast semantic search
- ✅ **Framework filter** — query one framework or all at once
- ✅ **Domain filter** — focus queries on specific compliance domains per framework
- ✅ **Dynamic suggested questions** — change based on selected framework
- ✅ **Source pages** — see exactly which PDF pages backed each answer
- ✅ **Streamlit UI** — clean, interactive chat interface
- ✅ **Publicly deployed** on Streamlit Community Cloud

---

## 🚀 Try it online

Visit the live app — no installation needed:

**👉 [https://sama-csf-chatbot-hx8aqfwx3appqe9qsh366x7.streamlit.app](https://sama-csf-chatbot-hx8aqfwx3appqe9qsh366x7.streamlit.app)**

1. Enter your **Anthropic API key** in the sidebar (get one free at [console.anthropic.com](https://console.anthropic.com/settings/keys))
2. Select a **framework** from the dropdown (SAMA CSF, PDPL, or NCA ECC)
3. Ask any compliance question
4. Get a structured answer with source page references

---

## 🏗️ How it works

```
Your compliance question
        ↓
Select framework (SAMA CSF / PDPL / NCA ECC)
        ↓
ChromaDB retrieves the 5 most relevant chunks filtered by framework
        ↓
Claude (claude-haiku-4-5) reads those chunks + your question
        ↓
Structured compliance answer + source page references
```

### Architecture: RAG (Retrieval Augmented Generation)

**1. Indexing (one-time setup)**
- Compliance PDFs are split into overlapping text chunks (1000 chars, 150 overlap)
- Each chunk is tagged with its framework name as metadata
- Chunks are embedded using HuggingFace `all-MiniLM-L6-v2` (free, local)
- All embeddings are stored in a single ChromaDB collection

**2. Querying (every user question)**
- The question is embedded using the same model
- ChromaDB does a semantic similarity search, filtered by selected framework
- Top-K most relevant chunks are retrieved
- Chunks are passed to Claude with a structured compliance prompt
- Claude generates a grounded, structured answer

---

## 🖥️ Run locally

### Prerequisites

| Requirement | Version | Notes |
|---|---|---|
| Python | 3.10 or higher | Check with `python --version` |
| Anthropic API key | Any tier | Free at [console.anthropic.com](https://console.anthropic.com/settings/keys) |
| Framework PDFs | Latest versions | See Step 2 below |

---

### Step 1 — Clone the repository

```bash
git clone https://github.com/Raza8386/sama-csf-chatbot.git
cd sama-csf-chatbot/sama_chatbot
```

---

### Step 2 — Download the compliance PDFs

Download each PDF and place it in the `sama_chatbot/` folder with the exact filename shown:

| Framework | Filename | Source |
|---|---|---|
| SAMA Cyber Security Framework | `sama_csf.pdf` | [SAMA website](https://www.sama.gov.sa/en-US/RulesInstructions/) |
| Personal Data Protection Law | `pdpl.pdf` | [SDAIA / NDMO website](https://sdaia.gov.sa/en/Regulatory/Pages/DataProtection.aspx) |
| NCA Essential Cybersecurity Controls | `nca_ecc.pdf` | [NCA website](https://nca.gov.sa/en/pages/ecc) |

> You can start with just one PDF — the app will work with whichever PDFs are present.

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

### Step 6 — Index the PDFs (run once)

```bash
python index_docs.py
```

This will:
- Detect which framework PDFs are present
- Split each PDF into chunks and tag with framework name
- Download the `all-MiniLM-L6-v2` embedding model (~90 MB, one-time)
- Save all embeddings to `sama_db/`

**Expected output:**
```
============================================================
  GRC Compliance Framework Indexer
============================================================
📋  Checking for framework PDFs...
    ✔  Found: sama_csf.pdf  (SAMA CSF)
    ✔  Found: pdpl.pdf  (PDPL)
    ✔  Found: nca_ecc.pdf  (NCA ECC)

📄  Loading: sama_csf.pdf  [SAMA CSF]
    ✔  Loaded 56 pages  →  171 chunks

📄  Loading: pdpl.pdf  [PDPL]
    ✔  Loaded 43 pages  →  138 chunks

📄  Loading: nca_ecc.pdf  [NCA ECC]
    ✔  Loaded 61 pages  →  193 chunks

📦  Total chunks across all frameworks: 502
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

**SAMA CSF**
- *"What are the maturity level 3 requirements for cybersecurity governance?"*
- *"What does SAMA CSF require for vulnerability management?"*
- *"How should third-party cybersecurity risk be managed?"*
- *"What controls are required for privileged access management?"*

**PDPL**
- *"What are the conditions for lawful data processing under PDPL?"*
- *"What are the rights of data subjects under PDPL?"*
- *"What are the penalties for PDPL violations?"*
- *"When is a Data Protection Officer required?"*

**NCA ECC**
- *"What are the NCA ECC requirements for identity and access management?"*
- *"How does NCA ECC address cybersecurity incident response?"*
- *"What are the asset management controls in NCA ECC?"*
- *"What does NCA ECC say about cloud security?"*

---

## 📁 Project structure

```
sama_chatbot/
├── app.py              ← Streamlit chatbot UI (main entry point)
├── index_docs.py       ← One-time PDF indexing script
├── chatbot_config.py   ← All settings in one place
├── requirements.txt    ← Python dependencies
├── runtime.txt         ← Python version for Streamlit Cloud
├── .env.example        ← Template for environment variables
├── .env                ← Your actual API key (not committed to Git)
├── .streamlit/
│   └── config.toml     ← Streamlit server settings
├── sama_csf.pdf        ← SAMA CSF PDF (place here)
├── pdpl.pdf            ← PDPL PDF (place here)
├── nca_ecc.pdf         ← NCA ECC PDF (place here)
└── sama_db/            ← ChromaDB vector index (auto-created)
```

---

## ⚙️ Configuration

All settings are in `chatbot_config.py`:

| Setting | Default | Description |
|---|---|---|
| `EMBEDDING_MODEL` | `all-MiniLM-L6-v2` | HuggingFace local embedding model |
| `LLM_MODEL` | `claude-haiku-4-5` | Anthropic Claude model |
| `CHUNK_SIZE` | `1000` | Characters per chunk |
| `CHUNK_OVERLAP` | `150` | Overlap between adjacent chunks |
| `TOP_K_RESULTS` | `5` | Chunks retrieved per query |
| `CHROMA_DB_PATH` | `./sama_db` | Vector database location |
| `COLLECTION_NAME` | `grc_frameworks` | ChromaDB collection name |

> If you change `CHUNK_SIZE` or `CHUNK_OVERLAP`, re-run `python index_docs.py` to rebuild the index.

---

## 🔍 Frameworks & Domains covered

### SAMA CSF
- Cybersecurity Leadership and Governance
- Cybersecurity Risk Management
- Cybersecurity Operations and Technology
- Third-Party Cybersecurity
- Cybersecurity Resilience
- Application Security
- Data and Cloud Security
- Industrial Systems Security

### PDPL
- Data Collection and Processing
- Personal Data Rights
- Consent and Legal Basis
- Data Retention and Destruction
- Cross-border Data Transfers
- Data Breach Notification
- Data Protection Officer
- Privacy Notice and Transparency

### NCA ECC
- Cybersecurity Governance
- Cybersecurity Risk Management
- Cybersecurity Operations
- Third-Party and Cloud Security
- Industrial Control Systems Security
- Cybersecurity Resilience
- Physical Security
- Asset Management
- Identity and Access Management
- Information Protection

---

## 🛠️ Troubleshooting

### `❌ ANTHROPIC_API_KEY is not set`
- Enter your key in the sidebar input field on the app
- Or add it to `.env`: `ANTHROPIC_API_KEY=sk-ant-...`

### `❌ PDF not found`
- Confirm the PDF is in the same folder as `index_docs.py`
- Filename must match exactly: `sama_csf.pdf`, `pdpl.pdf`, or `nca_ecc.pdf`

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
| Indexing all 3 frameworks (one-time) | **Free** — local embeddings |
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
| RAG Orchestration | LangChain LCEL (modern, no deprecated chains) |
| UI | Streamlit |
| Deployment | Streamlit Community Cloud |
| Version Control | GitHub |

---

## 👤 Author

**Danish Raza** — GRC Professional  
📧 danishraza786@gmail.com  
🔗 [github.com/Raza8386](https://github.com/Raza8386)

---

*Built with LangChain · ChromaDB · Anthropic Claude · HuggingFace · Streamlit*
