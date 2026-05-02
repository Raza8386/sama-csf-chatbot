"""
app.py - Streamlit chatbot UI for the SAMA CSF Compliance Assistant

Launch with:
    streamlit run app.py

This file handles:
  - Loading ChromaDB and the LLM chain
  - Sidebar controls (domain filter, source toggle, chunk slider)
  - Chat history with session state
  - Streaming LLM responses token by token
  - Expandable source document previews
"""

import os
import sys
import json
import streamlit as st
import streamlit.components.v1 as components

# Agent module (imported lazily inside render_agent_tab to avoid errors if
# the anthropic package is missing on first install)


# ── Page config must be the very first Streamlit call ────────────────────────
st.set_page_config(
    page_title="SAMA CSF Compliance Assistant",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Config import ─────────────────────────────────────────────────────────────
# Centralised settings — edit config.py, not this file
try:
    from chatbot_config import (
        ANTHROPIC_API_KEY,
        EMBEDDING_MODEL,
        LLM_MODEL,
        TOP_K_RESULTS,
        CHROMA_DB_PATH,
        COLLECTION_NAME,
        SAMA_DOMAINS,
        FRAMEWORK_DOMAINS,
        PDF_SOURCES,
        SYSTEM_PROMPT,
    )
except Exception as err:
    st.error(f"**Startup error:** {type(err).__name__}: {err}")
    st.stop()

# ── LangChain imports ─────────────────────────────────────────────────────────
try:
    from langchain_anthropic import ChatAnthropic
    from langchain_community.vectorstores import Chroma
    from langchain_core.prompts import ChatPromptTemplate
    try:
        from langchain_huggingface import HuggingFaceEmbeddings
    except ImportError:
        from langchain_community.embeddings import HuggingFaceEmbeddings
except Exception as import_err:
    st.error(f"**Package import error:** {type(import_err).__name__}: {import_err}")
    st.stop()


# ═══════════════════════════════════════════════════════════════════════════════
#  Helper functions
# ═══════════════════════════════════════════════════════════════════════════════

@st.cache_resource(show_spinner="Loading SAMA CSF knowledge base...")
def load_vector_store():
    """
    Load the ChromaDB vector store from disk (cached so it only loads once).
    Returns the Chroma object or None if the database has not been indexed yet.
    """
    sqlite_file = os.path.join(CHROMA_DB_PATH, "chroma.sqlite3")
    if not os.path.exists(sqlite_file):
        return None  # Signal to the UI that indexing hasn't been done

    embeddings = HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL,
    )

    vector_store = Chroma(
        persist_directory=CHROMA_DB_PATH,
        embedding_function=embeddings,
        collection_name=COLLECTION_NAME,
    )
    return vector_store


def build_rag_chain(vector_store: Chroma, top_k: int, selected_framework: str) -> tuple:
    """
    Build a retriever + LLM + prompt using modern LCEL.
    Filters ChromaDB by framework metadata when a specific framework is selected.
    Returns a (retriever, llm, prompt) tuple.
    """
    # Apply metadata filter when a specific framework is chosen
    if selected_framework and selected_framework != "All Frameworks":
        search_kwargs = {
            "k": top_k,
            "filter": {"framework": selected_framework},
        }
    else:
        search_kwargs = {"k": top_k}

    retriever = vector_store.as_retriever(
        search_type="similarity",
        search_kwargs=search_kwargs,
    )

    # Use key from sidebar input if provided, otherwise fall back to config/env
    api_key = st.session_state.get("api_key") or ANTHROPIC_API_KEY

    llm = ChatAnthropic(
        model=LLM_MODEL,
        temperature=0,
        anthropic_api_key=api_key,
    )

    prompt = ChatPromptTemplate.from_template(SYSTEM_PROMPT)

    return retriever, llm, prompt


def get_confidence_label(num_sources: int) -> tuple[str, str]:
    """
    Return a simple confidence label and colour based on how many
    relevant chunks were retrieved (more chunks = higher confidence).
    """
    if num_sources >= 4:
        return "High", "🟢"
    elif num_sources >= 2:
        return "Medium", "🟡"
    else:
        return "Low", "🔴"


def generate_followup_questions(llm, question: str, answer: str, framework: str) -> list:
    """
    Ask Claude to suggest 3 short follow-up compliance questions based on the
    current Q&A. Returns a list of strings (empty list on any failure).
    """
    from langchain_core.messages import HumanMessage

    prompt = (
        f"You are a GRC compliance advisor.\n"
        f"Framework: {framework}\n"
        f"Question asked: {question}\n"
        f"Answer provided: {answer[:600]}\n\n"
        "Suggest exactly 3 short, specific follow-up questions a GRC auditor "
        "might ask next. Rules:\n"
        "- Each question must be directly related to the topic above\n"
        "- Keep each question under 15 words\n"
        "- Return ONLY a valid JSON array of exactly 3 strings, nothing else\n\n"
        'Example: ["Question one?", "Question two?", "Question three?"]'
    )

    try:
        response = llm.invoke([HumanMessage(content=prompt)])
        content = response.content.strip()
        start = content.find("[")
        end = content.rfind("]") + 1
        if start >= 0 and end > start:
            questions = json.loads(content[start:end])
            return [q for q in questions if isinstance(q, str)][:3]
    except Exception:
        pass
    return []


def render_copy_button(text: str, key: str):
    """
    Render a 'Copy Answer' button that copies `text` to the clipboard via JS.
    Shows a brief '✅ Copied!' confirmation, then resets after 2 seconds.
    """
    escaped = (
        text.replace("\\", "\\\\")
            .replace("`", "\\`")
            .replace("${", "\\${")
    )
    components.html(
        f"""
        <button
            onclick="navigator.clipboard.writeText(`{escaped}`).then(() => {{
                this.innerHTML = '✅ Copied!';
                setTimeout(() => this.innerHTML = '📋 Copy Answer', 2000);
            }})"
            style="
                background:#f0f2f6;
                border:1px solid #d0d3d9;
                border-radius:6px;
                padding:4px 14px;
                cursor:pointer;
                font-size:13px;
                color:#31333f;
                margin-top:6px;
            "
        >📋 Copy Answer</button>
        """,
        height=42,
    )


def render_followup_chips(questions: list, msg_idx: int):
    """
    Render 2-3 follow-up question chips below an assistant answer.
    Clicking a chip sets it as the next question via session state.
    """
    if not questions:
        return
    st.markdown("**💬 You might also ask:**")
    for i, q in enumerate(questions):
        if st.button(q, key=f"followup_{msg_idx}_{i}", use_container_width=False):
            st.session_state.sidebar_question = q


def initialise_session_state():
    """Set up Streamlit session state keys on first load."""
    if "messages" not in st.session_state:
        st.session_state.messages = []       # Full chat history
    if "question_count" not in st.session_state:
        st.session_state.question_count = 0  # Total questions this session
    if "active_domains" not in st.session_state:
        st.session_state.active_domains = []  # Domain filter history per question


# ═══════════════════════════════════════════════════════════════════════════════
#  Sidebar
# ═══════════════════════════════════════════════════════════════════════════════

def render_sidebar(vector_store) -> tuple[str, list[str], bool, int]:
    """
    Render the left sidebar and return the user's current selections:
      - selected_framework: framework to filter by (or "All Frameworks")
      - selected_domains: list of domains to focus on
      - show_sources: whether to display source chunks below each answer
      - top_k: number of chunks to retrieve
    """
    with st.sidebar:
        # ── App branding ──────────────────────────────────────────────────────
        st.markdown("## 🛡️ GRC Compliance Assistant")
        st.markdown(
            "An AI-powered compliance advisor trained on multiple "
            "**Saudi regulatory frameworks**."
        )
        st.divider()

        # ── API Key input ─────────────────────────────────────────────────────
        st.subheader("🔑 Anthropic API Key")
        user_api_key = st.text_input(
            "Enter your Anthropic API key:",
            type="password",
            placeholder="sk-ant-...",
            help="Get your free key at https://console.anthropic.com/settings/keys",
        )
        if user_api_key:
            st.session_state.api_key = user_api_key
            st.success("✅ API key set")
        elif "api_key" not in st.session_state:
            st.warning("⚠️ Enter your Anthropic API key to start")

        st.divider()

        # ── Database status indicator ─────────────────────────────────────────
        if vector_store is not None:
            st.markdown("**Database status:** 🟢 Knowledge base loaded")
        else:
            st.markdown("**Database status:** 🔴 Not indexed yet")

        st.markdown(
            f"**Questions asked this session:** {st.session_state.question_count}"
        )
        st.divider()

        # ── About section ─────────────────────────────────────────────────────
        with st.expander("ℹ️ About this tool"):
            st.markdown(
                """
                This chatbot uses **RAG (Retrieval Augmented Generation)** to
                answer compliance questions from multiple regulatory frameworks.

                - Answers grounded in official PDFs — no hallucination
                - Source pages shown below each answer
                - Filter by framework and domain
                """
            )

        # ── Framework selector ────────────────────────────────────────────────
        st.subheader("📚 Framework")
        framework_options = ["All Frameworks"] + list(PDF_SOURCES.keys())
        selected_framework = st.selectbox(
            "Select a framework:",
            options=framework_options,
            help="Filter answers to a specific regulatory framework.",
        )

        # ── Domain filter (changes based on selected framework) ───────────────
        st.subheader("🔍 Domain Filter")
        st.caption("Optionally narrow to specific domains (leave blank for all).")

        if selected_framework == "All Frameworks":
            domain_options = SAMA_DOMAINS
        else:
            domain_options = FRAMEWORK_DOMAINS.get(selected_framework, [])

        selected_domains = st.multiselect(
            label="Focus on these domains:",
            options=domain_options,
            default=[],
            placeholder="All domains (no filter)",
        )

        st.divider()

        # ── Display options ───────────────────────────────────────────────────
        st.subheader("⚙️ Options")

        show_sources = st.toggle(
            "Show source documents",
            value=True,
            help="Display the raw PDF chunks used to generate the answer.",
        )

        top_k = st.slider(
            "Chunks to retrieve",
            min_value=3,
            max_value=10,
            value=TOP_K_RESULTS,
            help="More chunks = more context but slightly slower response.",
        )

        st.divider()

        # ── Suggested questions (always visible, changes with framework) ────────
        st.subheader("💡 Suggested Questions")
        questions = STARTER_QUESTIONS.get(selected_framework, STARTER_QUESTIONS["All Frameworks"])
        for i, q in enumerate(questions):
            if st.button(q, use_container_width=True, key=f"sidebar_q_{selected_framework}_{i}"):
                st.session_state.sidebar_question = q

        st.divider()

        # ── Clear conversation button ─────────────────────────────────────────
        if st.button("🗑️ Clear conversation", use_container_width=True):
            st.session_state.messages = []
            st.session_state.question_count = 0
            st.session_state.active_domains = []
            st.session_state.pop("sidebar_question", None)
            st.rerun()

    return selected_framework, selected_domains, show_sources, top_k


# ═══════════════════════════════════════════════════════════════════════════════
#  Starter question chips
# ═══════════════════════════════════════════════════════════════════════════════

STARTER_QUESTIONS = {
    "SAMA CSF": [
        "What are the maturity level 3 requirements for cybersecurity governance?",
        "What does SAMA CSF require for vulnerability management?",
        "How should third-party cybersecurity risk be managed?",
        "What are the incident response requirements?",
    ],
    "PDPL": [
        "What are the data subject rights under PDPL?",
        "What are the requirements for cross-border data transfers under PDPL?",
        "When is consent required for processing personal data?",
        "What are the breach notification obligations under PDPL?",
    ],
    "NCA ECC": [
        "What are the essential cybersecurity controls for identity management?",
        "What does NCA ECC require for cybersecurity governance?",
        "What are the asset management requirements in NCA ECC?",
        "How should cybersecurity incidents be handled under NCA ECC?",
    ],
    "All Frameworks": [
        "What are the incident response requirements?",
        "How should third-party risk be managed?",
        "What are the data protection obligations?",
        "What cybersecurity governance controls are required?",
    ],
}


def render_starter_chips(selected_framework: str) -> str | None:
    """
    Show clickable question chips relevant to the selected framework.
    Returns the selected question text, or None if none was clicked.
    """
    st.markdown("#### 💡 Suggested questions — click to ask:")

    questions = STARTER_QUESTIONS.get(selected_framework, STARTER_QUESTIONS["All Frameworks"])

    cols = st.columns(2)
    for index, question in enumerate(questions):
        col = cols[index % 2]
        with col:
            if st.button(question, use_container_width=True, key=f"starter_{index}"):
                return question
    return None


# ═══════════════════════════════════════════════════════════════════════════════
#  Source document display
# ═══════════════════════════════════════════════════════════════════════════════

def render_source_documents(source_docs: list, show_sources: bool):
    """
    Show an expandable section with the raw PDF chunks that backed the answer.
    Each entry shows the page number and the first 400 characters of the chunk.
    """
    if not show_sources or not source_docs:
        return

    confidence_label, confidence_icon = get_confidence_label(len(source_docs))

    # Confidence badge above the expander
    st.markdown(
        f"**Retrieval confidence:** {confidence_icon} {confidence_label} "
        f"({len(source_docs)} relevant chunks found)"
    )

    with st.expander("📄 Source pages from SAMA CSF", expanded=False):
        for idx, doc in enumerate(source_docs, start=1):
            # PyPDFLoader stores the 0-based page number in metadata
            page_num = doc.metadata.get("page", "unknown")
            # Show only the first 400 characters to keep the UI clean
            snippet = doc.page_content[:400].strip()
            if len(doc.page_content) > 400:
                snippet += "..."

            st.markdown(f"**Source {idx} — Page {page_num + 1}**")
            st.text(snippet)
            if idx < len(source_docs):
                st.divider()


# ═══════════════════════════════════════════════════════════════════════════════
#  Main chat area
# ═══════════════════════════════════════════════════════════════════════════════

def render_chat_history():
    """Replay every message in session state so the conversation persists on rerun."""

    # Find the index of the last assistant message (follow-ups shown only there)
    last_assistant_idx = None
    for i, msg in enumerate(st.session_state.messages):
        if msg["role"] == "assistant":
            last_assistant_idx = i

    for idx, message in enumerate(st.session_state.messages):
        role = message["role"]
        with st.chat_message(role):
            st.markdown(message["content"])

            if role == "assistant":
                # Re-render source documents stored alongside assistant messages
                if "source_docs" in message:
                    render_source_documents(
                        message["source_docs"],
                        show_sources=message.get("show_sources", True),
                    )

                # Copy button for every assistant message
                render_copy_button(message["content"], key=f"copy_{idx}")

                # Follow-up chips only for the most recent answer
                if idx == last_assistant_idx:
                    render_followup_chips(
                        message.get("followup_questions", []), idx
                    )


def ask_question(
    rag_chain: tuple,
    user_question: str,
    selected_framework: str,
    selected_domains: list[str],
    show_sources: bool,
):
    """
    Run the RAG chain for `user_question`, stream the response, then store
    both the question and answer in session state for conversation history.
    """
    retriever, llm, prompt = rag_chain

    # Build augmented question with framework and domain hints
    hints = []
    if selected_framework and selected_framework != "All Frameworks":
        hints.append(f"Framework: {selected_framework}")
    if selected_domains:
        hints.append(f"Domains: {', '.join(selected_domains)}")

    if hints:
        augmented_question = f"[{' | '.join(hints)}]\n\n{user_question}"
    else:
        augmented_question = user_question

    # Add user message to history and render it immediately
    st.session_state.messages.append({"role": "user", "content": user_question})
    with st.chat_message("user"):
        st.markdown(user_question)

    # Run the chain and stream the assistant response
    followup_questions = []
    with st.chat_message("assistant"):
        response_placeholder = st.empty()
        full_response = ""
        source_docs = []

        try:
            # Step 1: retrieve relevant chunks from ChromaDB
            source_docs = retriever.invoke(augmented_question)
            context = "\n\n".join(doc.page_content for doc in source_docs)

            # Step 2: format prompt and call Claude
            messages = prompt.format_messages(context=context, question=augmented_question)
            response = llm.invoke(messages)
            full_response = response.content

            # Display the response
            response_placeholder.markdown(full_response)

            # Show source documents below the answer
            render_source_documents(source_docs, show_sources)

            # Copy button
            render_copy_button(full_response, key="copy_live")

            # Generate and display follow-up question suggestions
            with st.spinner("Generating follow-up suggestions..."):
                followup_questions = generate_followup_questions(
                    llm, user_question, full_response, selected_framework
                )
            render_followup_chips(followup_questions, msg_idx=len(st.session_state.messages))

        except Exception as api_error:
            error_message = (
                "⚠️  An error occurred while querying the AI model.\n\n"
                f"**Error details:** {str(api_error)}\n\n"
                "Please check your Anthropic API key and internet connection, then try again."
            )
            response_placeholder.error(error_message)
            full_response = error_message

    # Persist the assistant response (and its sources) to session state
    st.session_state.messages.append({
        "role": "assistant",
        "content": full_response,
        "source_docs": source_docs,
        "show_sources": show_sources,
        "domains_filter": selected_domains,
        "followup_questions": followup_questions,
    })
    st.session_state.question_count += 1


# ═══════════════════════════════════════════════════════════════════════════════
#  Agent tab
# ═══════════════════════════════════════════════════════════════════════════════

def render_agent_tab(vector_store, selected_framework: str):
    """
    Render the Agent Mode tab.
    The user states a complex compliance goal; Claude autonomously searches
    the frameworks and produces a comprehensive answer.
    """
    st.markdown("### 🤖 Agent Mode")
    st.caption(
        "Give the agent a complex compliance goal. It will autonomously decide "
        "which frameworks to search, how many times, and when it has enough "
        "information to answer."
    )

    # ── Example goals ─────────────────────────────────────────────────────────
    with st.expander("💡 Example goals — click to expand"):
        st.markdown(
            """
- *"Compare incident response requirements across SAMA CSF, PDPL, and NCA ECC"*
- *"What do I need to reach SAMA CSF maturity level 3 in cybersecurity governance?"*
- *"Summarise all data subject rights under PDPL and map them to NCA ECC controls"*
- *"What are the third-party risk management requirements across all frameworks?"*
- *"List all penalties mentioned in PDPL and what triggers them"*
            """
        )

    # ── Goal input ────────────────────────────────────────────────────────────
    goal = st.text_area(
        "Enter your compliance goal:",
        placeholder=(
            "e.g. Compare how SAMA CSF and PDPL address data breach notification "
            "requirements and list the key differences..."
        ),
        height=130,
    )

    col_btn, col_info = st.columns([1, 4])
    with col_btn:
        run_clicked = st.button("🚀 Run Agent", type="primary", use_container_width=True)
    with col_info:
        st.caption("The agent may make 2–5 searches before answering. This takes ~10–20 seconds.")

    # ── Run the agent ─────────────────────────────────────────────────────────
    if run_clicked:
        if not goal.strip():
            st.warning("Please enter a compliance goal above.")
            return

        api_key = st.session_state.get("api_key") or ANTHROPIC_API_KEY
        if not api_key:
            st.error("Please enter your Anthropic API key in the sidebar first.")
            return

        try:
            from agent import run_grc_agent
        except Exception as import_err:
            st.error(f"Could not load agent module: {import_err}")
            return

        with st.spinner("🤖 Agent is researching your question..."):
            result = run_grc_agent(goal, vector_store, api_key)

        # ── Agent reasoning log ────────────────────────────────────────────
        if result["tool_calls"]:
            label = (
                f"🔍 Agent reasoning — "
                f"{result['iterations']} step(s), "
                f"{len(result['tool_calls'])} search(es) performed"
            )
            with st.expander(label, expanded=False):
                for i, call in enumerate(result["tool_calls"], 1):
                    st.markdown(f"**Step {i} — `{call['tool']}`**")
                    st.json(call["input"])
                    st.caption(f"Result preview: {call['result_preview']}")
                    if i < len(result["tool_calls"]):
                        st.divider()

        # ── Final answer ───────────────────────────────────────────────────
        st.markdown("---")
        st.markdown("### 📋 Agent Answer")
        st.markdown(result["answer"])
        render_copy_button(result["answer"], key="agent_copy")


# ═══════════════════════════════════════════════════════════════════════════════
#  App entry point
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    """Orchestrate the full Streamlit app layout and interaction flow."""

    # Set up session state keys on first load
    initialise_session_state()

    # Load the ChromaDB vector store (cached after first load)
    vector_store = load_vector_store()

    # Render sidebar and capture the user's filter/option selections
    selected_framework, selected_domains, show_sources, top_k = render_sidebar(vector_store)

    # ── Main area header ──────────────────────────────────────────────────────
    st.title("🛡️ GRC Compliance Assistant")
    st.caption("Powered by SAMA CSF · PDPL · and more — answers grounded in official frameworks")
    st.divider()

    # ── Guard: show warning if ChromaDB hasn't been indexed yet ───────────────
    if vector_store is None:
        st.warning(
            "**Knowledge base not found.** You need to index the SAMA CSF PDF first.\n\n"
            "**Steps to set up:**\n"
            "1. Download the SAMA Cyber Security Framework PDF\n"
            "2. Rename it to `sama_csf.pdf` and place it in this folder\n"
            "3. Open a terminal in this folder and run:\n"
            "   ```\n"
            "   python index_docs.py\n"
            "   ```\n"
            "4. Come back here once indexing is complete"
        )
        st.stop()

    # ── Guard: require API key ────────────────────────────────────────────────
    if not st.session_state.get("api_key") and not ANTHROPIC_API_KEY:
        st.info("👈 Enter your **Anthropic API key** in the sidebar to start chatting.")
        st.stop()

    # ── Tabs: Chat Mode vs Agent Mode ─────────────────────────────────────────
    chat_tab, agent_tab = st.tabs(["💬 Chat Mode", "🤖 Agent Mode"])

    # ── Chat tab ──────────────────────────────────────────────────────────────
    with chat_tab:
        # Build the RAG chain (rebuilt when top_k or framework changes)
        rag_chain = build_rag_chain(vector_store, top_k, selected_framework)

        # Render existing conversation
        render_chat_history()

        # Starter chips only when chat is empty
        if not st.session_state.messages:
            render_starter_chips(selected_framework)

        # Chat input — placeholder changes with selected framework
        if selected_framework == "All Frameworks":
            placeholder = "Ask a compliance question across all frameworks..."
        else:
            placeholder = f"Ask a {selected_framework} compliance question..."

        typed_question = st.chat_input(placeholder)

        # Sidebar question button takes priority, then typed input
        sidebar_question = st.session_state.pop("sidebar_question", None)
        active_question = typed_question or sidebar_question

        if active_question:
            ask_question(rag_chain, active_question, selected_framework, selected_domains, show_sources)
            st.rerun()

    # ── Agent tab ─────────────────────────────────────────────────────────────
    with agent_tab:
        render_agent_tab(vector_store, selected_framework)


if __name__ == "__main__":
    main()
