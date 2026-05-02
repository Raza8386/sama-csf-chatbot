"""
mcp_server.py - MCP (Model Context Protocol) server for GRC Compliance Search

Exposes your ChromaDB vector store as native tools that Claude Desktop
and Claude Code can call directly — no Streamlit UI needed.

── Setup ────────────────────────────────────────────────────────────────────
1. Install the MCP SDK (one-time):
       pip install "mcp[cli]"

2. Make sure the knowledge base is indexed:
       python index_docs.py

3. Test the server locally:
       mcp dev mcp_server.py

4. Add to Claude Desktop config (see INSTALL INSTRUCTIONS below).

── Tools exposed to Claude ──────────────────────────────────────────────────
  search_compliance_framework  — semantic search in one or all frameworks
  compare_all_frameworks       — side-by-side search across SAMA CSF, PDPL, NCA ECC
  list_frameworks_and_domains  — show available frameworks and their domains

── INSTALL INSTRUCTIONS ─────────────────────────────────────────────────────
Find your Claude Desktop config file:
  Windows : %APPDATA%\\Claude\\claude_desktop_config.json
  Mac     : ~/Library/Application Support/Claude/claude_desktop_config.json

Add this block (update the path to match your machine):

{
  "mcpServers": {
    "grc-compliance": {
      "command": "python",
      "args": ["C:/Users/Admin/SAMA CSF Chat bot/sama_chatbot/mcp_server.py"]
    }
  }
}

Save the file and restart Claude Desktop.
You will see a 🔌 icon confirming the server is connected.

── Usage examples in Claude Desktop ─────────────────────────────────────────
  "Search SAMA CSF for vulnerability management requirements"
  "What does PDPL say about cross-border data transfers?"
  "Compare incident response requirements across all frameworks"
  "What frameworks and domains are available?"
"""

import os
import sys

# ── Ensure the sama_chatbot folder is on the path ────────────────────────────
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# ── Config import ─────────────────────────────────────────────────────────────
try:
    from chatbot_config import (
        EMBEDDING_MODEL,
        CHROMA_DB_PATH,
        COLLECTION_NAME,
        FRAMEWORK_DOMAINS,
        PDF_SOURCES,
    )
except Exception as e:
    print(f"Error importing chatbot_config: {e}", file=sys.stderr)
    sys.exit(1)

# ── MCP + LangChain imports ───────────────────────────────────────────────────
try:
    from mcp.server.fastmcp import FastMCP
except ImportError:
    print(
        "MCP SDK not found. Install it with:  pip install 'mcp[cli]'",
        file=sys.stderr,
    )
    sys.exit(1)

try:
    try:
        from langchain_chroma import Chroma
    except ImportError:
        from langchain_community.vectorstores import Chroma
    try:
        from langchain_huggingface import HuggingFaceEmbeddings
    except ImportError:
        from langchain_community.embeddings import HuggingFaceEmbeddings
except ImportError as e:
    print(f"LangChain import error: {e}", file=sys.stderr)
    sys.exit(1)


# ═══════════════════════════════════════════════════════════════════════════════
#  Vector store (loaded once at startup)
# ═══════════════════════════════════════════════════════════════════════════════

def _load_vector_store():
    sqlite_file = os.path.join(CHROMA_DB_PATH, "chroma.sqlite3")
    if not os.path.exists(sqlite_file):
        raise FileNotFoundError(
            f"Knowledge base not found at {CHROMA_DB_PATH}. "
            "Run  python index_docs.py  first."
        )
    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
    return Chroma(
        persist_directory=CHROMA_DB_PATH,
        embedding_function=embeddings,
        collection_name=COLLECTION_NAME,
    )


print("Loading GRC knowledge base...", file=sys.stderr)
try:
    _vector_store = _load_vector_store()
    print("Knowledge base loaded ✔", file=sys.stderr)
except FileNotFoundError as e:
    print(f"Error: {e}", file=sys.stderr)
    sys.exit(1)


# ═══════════════════════════════════════════════════════════════════════════════
#  MCP server
# ═══════════════════════════════════════════════════════════════════════════════

mcp = FastMCP(
    name="GRC Compliance Assistant",
    instructions=(
        "You have access to a Saudi Arabian GRC compliance knowledge base covering "
        "SAMA CSF, PDPL, and NCA ECC. Use the search tools to find specific "
        "requirements, controls, or articles before answering compliance questions. "
        "Always cite the framework name and page number in your response."
    ),
)


# ── Tool 1: Search a single framework (or all) ────────────────────────────────

@mcp.tool()
def search_compliance_framework(
    query: str,
    framework: str = "All Frameworks",
    num_results: int = 5,
) -> str:
    """Search Saudi Arabian compliance frameworks for specific requirements.

    Args:
        query:       Natural language compliance question or keyword search.
        framework:   Which framework to search. Options:
                     'SAMA CSF'  — SAMA Cyber Security Framework
                     'PDPL'      — Personal Data Protection Law
                     'NCA ECC'   — NCA Essential Cybersecurity Controls
                     'All Frameworks' — search across all three (default)
        num_results: Number of relevant chunks to return (3–8, default 5).
                     Use more for broad topics, fewer for precise lookups.
    """
    search_kwargs: dict = {"k": num_results}
    if framework != "All Frameworks":
        if framework not in PDF_SOURCES:
            available = ", ".join(PDF_SOURCES.keys())
            return f"Unknown framework '{framework}'. Available: {available}"
        search_kwargs["filter"] = {"framework": framework}

    try:
        docs = _vector_store.similarity_search(query, **search_kwargs)
    except Exception as exc:
        return f"Search error: {exc}"

    if not docs:
        scope = framework if framework != "All Frameworks" else "any framework"
        return f"No relevant content found in {scope} for: '{query}'"

    parts = []
    for i, doc in enumerate(docs, 1):
        fw   = doc.metadata.get("framework", "Unknown")
        page = doc.metadata.get("page", "?")
        page_display = (page + 1) if isinstance(page, int) else page
        parts.append(
            f"[Result {i} | {fw} | Page {page_display}]\n"
            f"{doc.page_content.strip()}"
        )
    return "\n\n---\n\n".join(parts)


# ── Tool 2: Compare all frameworks on the same topic ─────────────────────────

@mcp.tool()
def compare_all_frameworks(topic: str, num_results_per_framework: int = 3) -> str:
    """Compare how SAMA CSF, PDPL, and NCA ECC address the same compliance topic.

    Returns results from all three frameworks side by side so you can identify
    overlaps, gaps, and differences.

    Args:
        topic:                     The compliance topic to compare (e.g.
                                   'incident response', 'data breach notification',
                                   'third-party risk management').
        num_results_per_framework: Chunks per framework (default 3).
    """
    frameworks = list(PDF_SOURCES.keys())   # ["SAMA CSF", "PDPL", "NCA ECC"]
    sections = []

    for fw in frameworks:
        try:
            docs = _vector_store.similarity_search(
                topic,
                k=num_results_per_framework,
                filter={"framework": fw},
            )
            if docs:
                chunks = []
                for doc in docs:
                    page = doc.metadata.get("page", "?")
                    page_display = (page + 1) if isinstance(page, int) else page
                    chunks.append(
                        f"  [Page {page_display}]\n  {doc.page_content.strip()[:500]}"
                    )
                sections.append(f"{'=' * 50}\n{fw}\n{'=' * 50}\n" + "\n\n".join(chunks))
            else:
                sections.append(f"{'=' * 50}\n{fw}\n{'=' * 50}\nNo relevant content found.")
        except Exception as exc:
            sections.append(f"{'=' * 50}\n{fw}\n{'=' * 50}\nSearch error: {exc}")

    return "\n\n".join(sections)


# ── Tool 3: List available frameworks and domains ─────────────────────────────

@mcp.tool()
def list_frameworks_and_domains() -> str:
    """List all available compliance frameworks and their domains.

    Use this to understand what topics are covered before searching,
    or to help the user select the right framework for their question.
    """
    lines = ["Available GRC frameworks and domains:\n"]
    for fw, domains in FRAMEWORK_DOMAINS.items():
        lines.append(f"📋 {fw}")
        for domain in domains:
            lines.append(f"   • {domain}")
        lines.append("")
    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════════════════
#  Entry point
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("Starting GRC Compliance MCP server...", file=sys.stderr)
    mcp.run(transport="stdio")
