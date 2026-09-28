from pathlib import Path

from langchain_core.documents import Document

from src.config.settings import DATA_DIR, KNOWLEDGE_BASE_PATH, KNOWLEDGE_BASE_DIR


def policy_paths() -> list[Path]:
    primary = sorted(KNOWLEDGE_BASE_PATH.glob("*.pdf"))
    if primary:
        return primary
    root_pdfs = sorted(DATA_DIR.glob("*.pdf"))
    if root_pdfs:
        return root_pdfs
    return sorted(KNOWLEDGE_BASE_DIR.glob("*.txt"))


def load_policy_documents() -> list[Document]:
    documents: list[Document] = []
    for path in policy_paths():
        if path.suffix.lower() == ".pdf":
            try:
                from pypdf import PdfReader
            except ImportError as exc:
                raise RuntimeError("pypdf is required to load PDF policy documents") from exc
            for page_number, page in enumerate(PdfReader(str(path)).pages, start=1):
                text = page.extract_text() or ""
                if text.strip():
                    documents.append(Document(
                        page_content=text,
                        metadata={
                            "source": path.name,
                            "filename": path.name,
                            "page": page_number,
                            "document_type": "policy",
                        },
                    ))
        else:
            documents.append(Document(
                page_content=path.read_text(encoding="utf-8"),
                metadata={"source": path.name, "filename": path.name, "page": 1, "document_type": "policy"},
            ))
    if not documents:
        raise FileNotFoundError(f"No policy PDFs or text files found in {KNOWLEDGE_BASE_PATH}")
    return documents