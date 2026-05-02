"""
agent.py - Agentic GRC compliance advisor using Claude tool use

Unlike the simple RAG chatbot (fixed pipeline), this agent:
  - Decides autonomously which framework(s) to search
  - Runs multiple searches if needed
  - Synthesises findings from across frameworks
  - Stops when it has enough information to answer

Tools available to the agent:
  - search_framework  : semantic search within one or all frameworks
  - compare_frameworks: side-by-side search across all 3 frameworks
"""

import json
from anthropic import Anthropic

try:
    from chatbot_config import LLM_MODEL
except Exception:
    LLM_MODEL = "claude-haiku-4-5"

# ── Tool definitions (sent to Claude so it knows what it can call) ────────────

AGENT_TOOLS = [
    {
        "name": "search_framework",
        "description": (
            "Search a compliance framework for relevant requirements, controls, "
            "or articles. Use this to find specific information from SAMA CSF, "
            "PDPL, NCA ECC, or all frameworks at once. Call this multiple times "
            "with different queries to get comprehensive coverage."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query to find relevant compliance content.",
                },
                "framework": {
                    "type": "string",
                    "enum": ["SAMA CSF", "PDPL", "NCA ECC", "All Frameworks"],
                    "description": (
                        "Which framework to search. Use 'All Frameworks' for "
                        "cross-framework topics."
                    ),
                },
                "num_results": {
                    "type": "integer",
                    "description": "Number of chunks to retrieve (3–8). Use more for broad topics.",
                },
            },
            "required": ["query", "framework"],
        },
    },
    {
        "name": "compare_frameworks",
        "description": (
            "Compare how all three frameworks (SAMA CSF, PDPL, NCA ECC) address "
            "the same compliance topic. Returns results from every framework side "
            "by side. Use this when the user wants a cross-framework comparison."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "topic": {
                    "type": "string",
                    "description": "The compliance topic to compare across all frameworks.",
                }
            },
            "required": ["topic"],
        },
    },
]

# ── System prompt ─────────────────────────────────────────────────────────────

AGENT_SYSTEM_PROMPT = """You are an expert GRC (Governance, Risk and Compliance) agent specialising in Saudi Arabian regulations: SAMA Cyber Security Framework (CSF), the Personal Data Protection Law (PDPL), and the NCA Essential Cybersecurity Controls (ECC).

You have tools to search these frameworks. Use them intelligently:
- Search multiple times with different queries to get comprehensive coverage
- Use compare_frameworks when the user wants cross-framework differences
- Always cite the framework name and page number for every finding
- Be thorough but efficient — stop searching once you have enough information

Structure your final answer clearly:
- Framework name + relevant section / article / control reference
- Specific requirement or obligation
- Practical implementation guidance
- Penalties, maturity levels, or timelines if mentioned

If no relevant information is found after searching, say so clearly rather than guessing."""


# ═══════════════════════════════════════════════════════════════════════════════
#  Tool execution
# ═══════════════════════════════════════════════════════════════════════════════

def _search_framework(
    query: str,
    framework: str,
    num_results: int,
    vector_store,
) -> str:
    """Semantic search in ChromaDB, optionally filtered to one framework."""
    if framework == "All Frameworks":
        search_kwargs = {"k": num_results}
    else:
        search_kwargs = {"k": num_results, "filter": {"framework": framework}}

    try:
        docs = vector_store.similarity_search(query, **search_kwargs)
    except Exception as exc:
        return f"Search error: {exc}"

    if not docs:
        return f"No relevant content found in {framework} for query: '{query}'"

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


def _compare_frameworks(topic: str, vector_store) -> str:
    """Search all 3 frameworks for the same topic and return combined results."""
    frameworks = ["SAMA CSF", "PDPL", "NCA ECC"]
    sections = []

    for fw in frameworks:
        try:
            docs = vector_store.similarity_search(
                topic, k=3, filter={"framework": fw}
            )
            if docs:
                chunks = []
                for doc in docs:
                    page = doc.metadata.get("page", "?")
                    page_display = (page + 1) if isinstance(page, int) else page
                    chunks.append(
                        f"  [Page {page_display}] {doc.page_content.strip()[:400]}"
                    )
                sections.append(f"=== {fw} ===\n" + "\n\n".join(chunks))
            else:
                sections.append(f"=== {fw} ===\nNo relevant content found.")
        except Exception as exc:
            sections.append(f"=== {fw} ===\nError: {exc}")

    return "\n\n".join(sections)


def execute_tool(tool_name: str, tool_input: dict, vector_store) -> str:
    """Dispatch a tool call to the correct function."""
    if tool_name == "search_framework":
        return _search_framework(
            query=tool_input["query"],
            framework=tool_input.get("framework", "All Frameworks"),
            num_results=tool_input.get("num_results", 5),
            vector_store=vector_store,
        )
    if tool_name == "compare_frameworks":
        return _compare_frameworks(
            topic=tool_input["topic"],
            vector_store=vector_store,
        )
    return f"Unknown tool: {tool_name}"


# ═══════════════════════════════════════════════════════════════════════════════
#  Agent loop
# ═══════════════════════════════════════════════════════════════════════════════

def run_grc_agent(
    user_goal: str,
    vector_store,
    api_key: str,
    max_iterations: int = 10,
) -> dict:
    """
    Run the GRC agent for a given user goal.

    Returns a dict:
      {
        "answer"     : str,          # Claude's final answer
        "tool_calls" : list[dict],   # Log of every tool call made
        "iterations" : int,          # Number of Claude API calls made
      }
    """
    client   = Anthropic(api_key=api_key)
    messages = [{"role": "user", "content": user_goal}]
    tool_log = []
    iterations = 0

    while iterations < max_iterations:
        iterations += 1

        response = client.messages.create(
            model=LLM_MODEL,
            max_tokens=4096,
            system=AGENT_SYSTEM_PROMPT,
            tools=AGENT_TOOLS,
            messages=messages,
        )

        # ── Claude finished — extract the final text ──────────────────────────
        if response.stop_reason == "end_turn":
            final_text = "".join(
                block.text
                for block in response.content
                if hasattr(block, "text")
            )
            return {
                "answer": final_text,
                "tool_calls": tool_log,
                "iterations": iterations,
            }

        # ── Claude wants to call tools ────────────────────────────────────────
        if response.stop_reason == "tool_use":
            # Add Claude's turn (with tool_use blocks) to the conversation
            messages.append({"role": "assistant", "content": response.content})

            # Execute every tool call Claude requested
            tool_results = []
            for block in response.content:
                if block.type != "tool_use":
                    continue

                result = execute_tool(block.name, block.input, vector_store)

                # Keep a human-readable log for the UI
                tool_log.append({
                    "tool":           block.name,
                    "input":          block.input,
                    "result_preview": result[:300] + "…" if len(result) > 300 else result,
                })

                tool_results.append({
                    "type":        "tool_result",
                    "tool_use_id": block.id,
                    "content":     result,
                })

            # Feed all results back to Claude
            messages.append({"role": "user", "content": tool_results})

        else:
            # Unexpected stop reason — bail out
            break

    return {
        "answer": (
            "The agent reached its iteration limit without completing. "
            "Please try a more specific goal."
        ),
        "tool_calls": tool_log,
        "iterations": iterations,
    }
