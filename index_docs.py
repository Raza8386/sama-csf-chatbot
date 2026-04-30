"""
index_docs.py - One-time script to load the SAMA CSF PDF into ChromaDB

Run this ONCE before starting the chatbot:
    python index_docs.py

What it does:
  1. Checks that sama_csf.pdf exists
  2. Asks whether to skip if a database already exists
  3. Reads and splits the PDF into chunks
  4. Embeds each chunk using OpenAI
  5. Saves everything to a local ChromaDB folder (./sama_db)
"""

import os
import sys

# ── Config import ────────────────────────────────────────────────────────────
# All settings (paths, models, chunk sizes) come from config.py
try:
    from config import (
        ANTHROPIC_API_KEY,
        EMBEDDING_MODEL,
        CHUNK_SIZE,
        CHUNK_OVERLAP,
        CHROMA_DB_PATH,
        COLLECTION_NAME,
        PDF_PATH,
    )
except EnvironmentError as env_err:
    # config.py raises a clear error if ANTHROPIC_API_KEY is missing
    print(env_err)
    sys.exit(1)

# ── LangChain imports ────────────────────────────────────────────────────────
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma


def check_pdf_exists(pdf_path: str) -> bool:
    """Verify the SAMA CSF PDF is present. Print download instructions if not."""
    if os.path.isfile(pdf_path):
        return True

    print("\n❌  PDF not found:", pdf_path)
    print("\nTo download the SAMA Cyber Security Framework:")
    print("  1. Visit https://www.sama.gov.sa/en-US/RulesInstructions/")
    print("  2. Search for 'Cyber Security Framework'")
    print("  3. Download the PDF and rename it to 'sama_csf.pdf'")
    print("  4. Place it in the sama_chatbot/ folder (same folder as this script)")
    print("\nAlternatively, search Google for: 'SAMA Cyber Security Framework PDF'\n")
    return False


def check_existing_database(db_path: str) -> bool:
    """
    Check if a ChromaDB database already exists at the configured path.
    Ask the user whether to re-index or skip.
    Returns True if we should proceed with indexing, False to skip.
    """
    # ChromaDB creates a 'chroma.sqlite3' file when it initialises
    sqlite_file = os.path.join(db_path, "chroma.sqlite3")

    if not os.path.exists(sqlite_file):
        # No existing database — safe to create fresh
        return True

    print(f"\n⚠️  An existing ChromaDB database was found at: {db_path}")
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


def load_and_split_pdf(pdf_path: str) -> list:
    """
    Load the PDF with PyPDFLoader (one Document per page) then split
    each page into smaller overlapping chunks for better retrieval accuracy.
    """
    print(f"\n📄  Loading PDF: {pdf_path}")
    loader = PyPDFLoader(pdf_path)

    # Load returns a list of Document objects (one per PDF page)
    pages = loader.load()
    print(f"    ✔  Loaded {len(pages)} pages from PDF")

    # Split pages into smaller chunks so the LLM receives focused context
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        # Try to split on paragraph/sentence boundaries before cutting mid-word
        separators=["\n\n", "\n", ". ", " ", ""],
    )

    chunks = text_splitter.split_documents(pages)
    print(f"    ✔  Split into {len(chunks)} chunks "
          f"(size={CHUNK_SIZE}, overlap={CHUNK_OVERLAP})")
    return chunks


def build_vector_store(chunks: list) -> Chroma:
    """
    Embed each chunk using a local HuggingFace model and store in ChromaDB.
    Runs entirely on your machine — no API calls, no cost.
    First run downloads the model (~90 MB); subsequent runs use the cache.
    """
    print(f"\n🔢  Creating embeddings with model: {EMBEDDING_MODEL}")
    print("    Running locally via sentence-transformers (no API calls)...")
    print("    First run will download the model (~90 MB) — please wait...")

    # Initialise the local HuggingFace embedding model
    embeddings = HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL,
    )

    print(f"\n💾  Saving vector store to: {CHROMA_DB_PATH}")

    # Chroma.from_documents embeds all chunks and persists to disk in one call
    vector_store = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=CHROMA_DB_PATH,
        collection_name=COLLECTION_NAME,
    )

    print(f"    ✔  Vector store saved at: {CHROMA_DB_PATH}")
    return vector_store


def main():
    """Main indexing workflow — runs all steps in order with clear status output."""
    print("=" * 60)
    print("  SAMA CSF Document Indexer")
    print("=" * 60)

    # Step 1: Make sure the PDF is present
    if not check_pdf_exists(PDF_PATH):
        sys.exit(1)

    # Step 2: Check for an existing database and get user preference
    should_index = check_existing_database(CHROMA_DB_PATH)
    if not should_index:
        print("\n🚀  You can now launch the chatbot with:")
        print("       streamlit run app.py\n")
        sys.exit(0)

    # Step 3: Load and chunk the PDF
    chunks = load_and_split_pdf(PDF_PATH)

    # Step 4: Embed and store in ChromaDB
    vector_store = build_vector_store(chunks)

    # Step 5: Print a summary so the user knows everything worked
    print("\n" + "=" * 60)
    print("  ✅  Indexing Complete!")
    print("=" * 60)
    print(f"  📄  Pages loaded    : {len(chunks)} chunks created")
    print(f"  📦  Storage location: {CHROMA_DB_PATH}")
    print(f"  🗂️  Collection name : {COLLECTION_NAME}")
    print(f"  🤖  Embedding model : {EMBEDDING_MODEL}")
    print("\n  Next step — launch the chatbot:")
    print("       streamlit run app.py\n")


if __name__ == "__main__":
    main()
