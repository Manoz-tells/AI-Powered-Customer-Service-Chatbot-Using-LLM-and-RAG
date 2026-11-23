import json
from pathlib import Path

from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document


PROJECT_ROOT = Path(__file__).resolve().parent.parent
KB_DIR = PROJECT_ROOT / "knowledge_base"
INDEX_DIR = PROJECT_ROOT / "faiss_kb_index"
METADATA_FILE = KB_DIR / "metadata.json"


DEFAULT_METADATA = {
    "version": "1.0",
    "product": "unknown",
    "region": "global",
    "access_level": "public",
    "effective_date": "1900-01-01",
    "expiry_date": "2099-12-31"
}


def load_metadata():
    if not METADATA_FILE.exists():
        print("[ERROR] metadata.json not found.")
        return {}

    try:
        with open(METADATA_FILE, "r", encoding="utf-8") as file:
            return json.load(file)
    except Exception as error:
        print(f"[ERROR] Could not load metadata.json: {error}")
        return {}


def load_knowledge_base():
    metadata_map = load_metadata()

    documents = []

    for file_path in KB_DIR.glob("*.txt"):
        if file_path.name == "manifest.txt":
            continue
        filename = file_path.name

        try:
            content = file_path.read_text(encoding="utf-8").strip()

            if not content:
                print(f"[SKIP] Empty file: {filename}")
                continue

            metadata = DEFAULT_METADATA.copy()

            if filename in metadata_map:
                metadata.update(metadata_map[filename])
            else:
                print(
                    f"[WARNING] No metadata found for {filename}. "
                    f"Using safe defaults."
                )

            metadata["source"] = filename

            document = Document(
                page_content=content,
                metadata=metadata
            )

            documents.append(document)

            print(
                f"[LOADED] {filename} | "
                f"access={metadata['access_level']} | "
                f"effective={metadata['effective_date']} | "
                f"expiry={metadata['expiry_date']}"
            )

        except Exception as error:
            print(f"[ERROR] Could not process {filename}: {error}")

    return documents


def build_faiss_index():
    documents = load_knowledge_base()

    if not documents:
        print("[ERROR] No knowledge-base documents found.")
        return

    print(f"\nBuilding FAISS index from {len(documents)} documents...")

    embeddings = HuggingFaceEmbeddings(
        model_name="hkunlp/instructor-large"
    )

    vectorstore = FAISS.from_documents(
        documents,
        embeddings
    )

    vectorstore.save_local(str(INDEX_DIR))

    print("\n[SUCCESS] FAISS knowledge-base index created.")
    print(f"Index location: {INDEX_DIR}")

    print("\nStored metadata:")

    for document in documents:
        print(document.metadata)


if __name__ == "__main__":
    build_faiss_index()