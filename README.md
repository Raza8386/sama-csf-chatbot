# 🛡️ GRC Compliance Assistant

An AI-powered GRC compliance tool covering **SAMA Cyber Security Framework (CSF)**, **Personal Data Protection Law (PDPL)**, and **NCA Essential Cybersecurity Controls (ECC)**. Offers two modes — a RAG-powered chatbot for quick questions and an **Agentic AI** mode for complex, multi-step compliance goals.

🌐 **Live Demo:** [sama-csf-chatbot.streamlit.app](https://sama-csf-chatbot-hx8aqfwx3appqe9qsh366x7.streamlit.app)

---

## 📸 Features

### 💬 Chat Mode (RAG Chatbot)
- ✅ **RAG-powered answers** grounded in official compliance documents
- ✅ **Claude AI** (`claude-haiku-4-5`) for structured compliance responses
- ✅ **Framework filter** — query SAMA CSF, PDPL, NCA ECC, or all at once
- ✅ **Domain filter** — focus queries on specific compliance domains per framework
- ✅ **Dynamic suggested questions** — change based on selected framework
- ✅ **Follow-up question suggestions** — Claude suggests 3 related questions after each answer
- ✅ **Copy Answer button** — one-click clipboard copy for audit reports
- ✅ **Source pages** — see exactly which PDF pages backed each answer
- ✅ **Retrieval confidence** — High / Medium / Low based on chunks retrieved

### 🤖 Agent Mode (Agentic AI)
- ✅ **Claude tool use** — Claude autonomously decides which frameworks to search
- ✅ **Multi-step reasoning** — agent runs multiple searches until it has enough information
- ✅ **Two tools**: `search_framework` and `compare_frameworks`
- ✅ **Reasoning log** — see every search the agent made and why
- ✅ **Complex goal support** — gap assessments, cross-framework comparisons, deep dives
- ✅ **Copy Answer button** on the final agent response

### General
- ✅ **Multi-framework support** — SAMA CSF, PDPL, and NCA ECC in one app
- ✅ **Local embeddings** via HuggingFace `all-MiniLM-L6-v2` — free, no API cost
- ✅ **ChromaDB** vector database for fast semantic search
- ✅ **Publicly deployed** on Streamlit Community Cloud

---

## 🚀 Try it online

**👉 [https://sama-csf-chatbot-hx8aqfwx3appqe9qsh366x7.streamlit.app](https://sama-csf-chatbot-hx8aqfwx3appqe9qsh366x7.streamlit.app)**

1. Enter your **Anthropic API key** in the sidebar (get one free at [console.anthropic.com](https://console.anthropic.com/settings/keys))
2. Choose **💬 Chat Mode** for quick questions or **🤖 Agent Mode** for complex goals
3. Select a framework and ask away

---

## 🏗️ How it works

### 💬 Chat Mode — RAG Pipeline (fixed, code-controlled)

```
User question
      ↓
ChromaDB retrieves the 5 most relevant chunks (filtered by framework)
      ↓
Claude reads chunks + question → structured compliance answer
      ↓
Claude suggests 3 follow-up questions
```

### 🤖 Agent Mode — Agentic Loop (Claude-controlled)

```
User states a complex compliance goal
      ↓
Claude decides: which tool to call? which framework? what query?
      ↓
Tool executes → result returned to Claude
      ↓
Claude decides: do I need more searches, or is this enough?
      ↓  (repeats until Claude is satisfied)
Claude writes final structured answer
```

**The key difference:** In Chat Mode, *your code* drives every step. In Agent Mode, *Claude* drives the process — choosing tools, forming queries, and deciding when it's done.

---

## 🤖 Agent Tools

| Tool | What it does |
|---|---|
| `search_framework` | Semantic search in one framework or across all three |
| `compare_frameworks` | Searches all 3 frameworks for the same topic and returns results side by side |

### Example agent goals
- *"Compare incident response requirements across SAMA CSF, PDPL, and NCA ECC"*
- *"What do I need to reach SAMA CSF maturity level 3 in cybersecurity governance?"*
- *"Summarise all data subject rights under PDPL and map them to NCA ECC controls"*
- *"What are the third-party risk management requirements across all frameworks?"*
- *"List all penalties mentioned in PDPL and what triggers them"*

---

## 🖥️ Run locally

### Prerequisites

| Requirement | Version | Notes |
|---|---|---|
| Python | 3.10 or higher | Check with `python --version` |
| Anthropic API key | Any tier | Free at [console.anthropic.com](https://console.anthropic.com/settings/keys) |
| Framework PDFs | Latest versions | See Step 2 below |

### Step 1 — Clone the repository

```bash
git clone https://github.com/Raza8386/sama-csf-chatbot.git
cd sama-csf-chatbot/sama_chatbot
```

### Step 2 — Download the compliance PDFs

Place each PDF in the `sama_chatbot/` folder with the exact filename shown:

| Framework | Filename | Source |
|---|---|---|
| SAMA Cyber Security Framework | `sama_csf.pdf` | [SAMA website](https://www.sama.gov.sa/en-US/RulesInstructions/) |
| Personal Data Protection Law | `pdpl.pdf` | [SDAIA / NDMO website](https://sdaia.gov.sa/en/Regulatory/Pages/DataProtection.aspx) |
| NCA Essential Cybersecurity Controls | `nca_ecc.pdf` | [NCA website](https://nca.gov.sa/en/pages/ecc) |

> You can start with just one PDF — the app works with whichever PDFs are present.

### Step 3 — Create your `.env` file

```bash
cp .env.example .env   # Mac/Linux
copy .env.example .env  # Windows
```

Add your key:
```
ANTHROPIC_API_KEY=sk-ant-...
```

### Step 4 — Install dependencies

```bash
pip install -r requirements.txt
```

### Step 5 — Index the PDFs (run once)

```bash
python index_docs.py
```

This loads all PDFs, splits them into chunks, tags each chunk with its framework name, and saves everything to ChromaDB.

### Step 6 — Launch the app

```bash
python -m streamlit run app.py
```

Open your browser at **http://localhost:8501**

---

## 📁 Project structure

```
sama_chatbot/
├── app.py              ← Streamlit UI — Chat Mode + Agent Mode tabs
├── agent.py            ← Agentic loop — Claude tool use, search tools
├── index_docs.py       ← One-time PDF indexing script
├── chatbot_config.py   ← All settings in one place
├── requirements.txt    ← Python dependencies
├── runtime.txt         ← Python version for Streamlit Cloud
├── .env.example        ← Template for environment variables
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
| `LLM_MODEL` | `claude-haiku-4-5` | Anthropic Claude model (used in both modes) |
| `CHUNK_SIZE` | `1000` | Characters per chunk |
| `CHUNK_OVERLAP` | `150` | Overlap between adjacent chunks |
| `TOP_K_RESULTS` | `5` | Chunks retrieved per query (Chat Mode) |

---

## 🔍 Frameworks & Domains

### SAMA CSF
- Cybersecurity Leadership and Governance · Cybersecurity Risk Management
- Cybersecurity Operations and Technology · Third-Party Cybersecurity
- Cybersecurity Resilience · Application Security · Data and Cloud Security · Industrial Systems Security

### PDPL
- Data Collection and Processing · Personal Data Rights · Consent and Legal Basis
- Data Retention and Destruction · Cross-border Data Transfers
- Data Breach Notification · Data Protection Officer · Privacy Notice and Transparency

### NCA ECC
- Cybersecurity Governance · Cybersecurity Risk Management · Cybersecurity Operations
- Third-Party and Cloud Security · Industrial Control Systems Security
- Cybersecurity Resilience · Physical Security · Asset Management
- Identity and Access Management · Information Protection

---

## 🛠️ Troubleshooting

| Error | Fix |
|---|---|
| `ANTHROPIC_API_KEY is not set` | Enter key in sidebar or add to `.env` |
| `PDF not found` | Confirm filename matches exactly in `sama_chatbot/` folder |
| `Knowledge base not loaded` | Run `python index_docs.py` first |
| `ModuleNotFoundError` | Run `pip install -r requirements.txt` |
| `invalid x-api-key` | Create a new key at [console.anthropic.com](https://console.anthropic.com/settings/keys) |

---

## 💰 Cost estimate

| Operation | Cost |
|---|---|
| Indexing all 3 frameworks (one-time) | **Free** — local embeddings |
| Chat Mode — per question | ~$0.001–0.005 |
| Agent Mode — per goal (2–5 searches) | ~$0.005–0.02 |
| 100 questions/month | ~$0.10–$2.00 |

---

## 🧰 Tech stack

| Component | Technology |
|---|---|
| LLM | Anthropic Claude (`claude-haiku-4-5`) |
| Agentic loop | Anthropic SDK — Claude tool use |
| Embeddings | HuggingFace `all-MiniLM-L6-v2` (local, free) |
| Vector DB | ChromaDB (local) |
| RAG Orchestration | LangChain LCEL |
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
