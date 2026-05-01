"""
index_docs.py - Index one or more compliance framework PDFs into ChromaDB

Run this ONCE (or whenever you add a new framework PDF):
    python index_docs.py

What it does:
  1. Checks which framework PDFs are present in the folder
  2. Loads and splits each PDF into chunks
  3. Tags every chunk with its framework name (e.g. "SAMA CSF", "PDPL")
  4. Embeds all chunks using a local HuggingFace model (free, no API)
  5. Saves everything to a single ChromaDB collection (./sama_db)
"""

import os
import sys

# ── Config import ────────────────────────────────────────────────────────────
try:
    from config import (
        ANTHROPIC_API_KEY,
        EMBEDDING_MODEL,
        CHUNK_SIZE,
        CHUNK_OVERLAP,
        CHROMA_DB_PATH,
        COLLECTION_NAME,
        PDF_SOURCES,
    )
except EnvironmentError as env_err:
    print(env_err)
    sys.exit(1)

# ── LangChain imports ────────────────────────────────────────────────────────
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma


def find_available_pdfs() -> dict:
    """
    Check which framework PDFs from PDF_SOURCES are actually present.
    Returns only the ones found on disk.
    """
    available = {}
    missing = []

    print("\n📋  Checking for framework PDFs...")
    for framework, filename in PDF_SOURCES.items():
        if os.path.isfile(filename):
            available[framework] = filename
            print(f"    ✔  Found: {filename}  ({framework})")
        else:
            missing.append((framework, filename))
            print(f"    ⚠️  Missing: {filename}  ({framework})")

    if missing:
        print("\n💡  To add missing frameworks, download the PDF and place it here:")
        for framework, filename in missing:
            print(f"       {filename}  ←  {framework}")

    if not available:
        print("\n❌  No PDFs found. Please add at least one framework PDF.")
        sys.exit(1)

    return available


def check_existing_database(db_path: str) -> bool:
    """
    Check if a ChromaDB database already exists.
    Ask the user whether to re-index or skip.
    Returns True to proceed with indexing, False to skip.
    """
    sqlite_file = os.path.join(db_path, "chroma.sqlite3")

    if not os.path.exists(sqlite_file):
        return True

    print(f"\n⚠️  Existing database found at: {db_path}")
    print("Options:")
    print("  [1] Re-index (overwrites the existing database)")
    print("  [2] Skip indexing (use the existing database as-is)")

    while True:
        choice = input("\nEnter 1 or 2: ").strip()
        if choice == "1":
            print("\n🗑️  Existing database will be overwritten.")
            return True
        elif choice == "2":
            print("\n✅  Skipping indexing. The existing database will be used.")
            return False
        else:
            print("Please enter 1 or 2.")


def load_and_split_pdf(framework: str, pdf_path: str) -> list:
    """
    Load a PDF and split into overlapping chunks.
    Each chunk is tagged with its framework name in metadata.
    """
    print(f"\n📄  Loading: {pdf_path}  [{framework}]")
    loader = PyPDFLoader(pdf_path)
    pages = loader.load()
    print(f"    ✔  Loaded {len(pages)} pages")

    # Tag every page with its framework so we can filter later
    for page in pages:
        page.metadata["framework"] = framework

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", " ", ""],
    )

    chunks = text_splitter.split_documents(pages)

    # Make sure the framework tag is on every chunk too
    for chunk in chunks:
        chunk.metadata["framework"] = framework

    print(f"    ✔  Split into {len(chunks)} chunks")
    return chunks


def build_vector_store(all_chunks: list) -> Chroma:
    """
    Embed all chunks using a local HuggingFace model and store in ChromaDB.
    Runs entirely on your machine — no API calls, no cost.
    """
    print(f"\n🔢  Creating embeddings with model: {EMBEDDING_MODEL}")
    print("    Running locally — no API calls, no cost.")
    print("    First run downloads the model (~90 MB)...")

    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)

    print(f"\n💾  Saving vector store to: {CHROMA_DB_PATH}")

    vector_store = Chroma.from_documents(
        documents=all_chunks,
        embedding=embeddings,
        persist_directory=CHROMA_DB_PATH,
        collection_name=COLLECTION_NAME,
    )

    print(f"    ✔  Vector store saved at: {CHROMA_DB_PATH}")
    return vector_store


def main():
    print("=" * 60)
    print("  GRC Compliance Framework Indexer")
    print("=" * 60)

    # Step 1: Find which PDFs are available
    available_pdfs = find_available_pdfs()

    # Step 2: Check for existing database
    should_index = check_existing_database(CHROMA_DB_PATH)
    if not should_index:
        print("\n🚀  Launch the chatbot with:")
        print("       python -m streamlit run app.py\n")
        sys.exit(0)

    # Step 3: Load and chunk all available PDFs
    all_chunks = []
    for framework, pdf_path in available_pdfs.items():
        chunks = load_and_split_pdf(framework, pdf_path)
        all_chunks.extend(chunks)

    print(f"\n📦  Total chunks across all frameworks: {len(all_chunks)}")

    # Step 4: Embed and store in ChromaDB
    build_vector_store(all_chunks)

    # Step 5: Summary
    print("\n" + "=" * 60)
    print("  ✅  Indexing Complete!")
    print("=" * 60)
    for framework, pdf_path in available_pdfs.items():
        print(f"  ✔  {framework}: {pdf_path}")
    print(f"\n  📦  Total chunks  : {len(all_chunks)}")
    print(f"  💾  Storage       : {CHROMA_DB_PATH}")
    print(f"  🗂️  Collection    : {COLLECTION_NAME}")
    print(f"  🤖  Embedding     : {EMBEDDING_MODEL}")
    print("\n  Next step — launch the chatbot:")
    print("       python -m streamlit run app.py\n")


if __name__ == "__main__":
    main()
