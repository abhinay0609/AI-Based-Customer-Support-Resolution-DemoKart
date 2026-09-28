from src.config.settings import KNOWLEDGE_BASE_DIR, VECTOR_DB_DIR


def ingest_policy() -> str:
    """Build the Chroma collection when optional LangChain dependencies are installed."""
    from langchain_chroma import Chroma
    from langchain_google_genai import GoogleGenerativeAIEmbeddings
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    from src.config.settings import GOOGLE_API_KEY
    from langchain_core.documents import Document

    policy_documents = [
        Document(
            page_content=policy_path.read_text(encoding="utf-8"),
            metadata={"source": policy_path.name},
        )
        for policy_path in sorted(KNOWLEDGE_BASE_DIR.glob("*.txt"))
    ]
    if not policy_documents:
        raise FileNotFoundError(f"No policy documents found in {KNOWLEDGE_BASE_DIR}")

    chunks = RecursiveCharacterTextSplitter(
        chunk_size=700,
        chunk_overlap=100,
    ).split_documents(policy_documents)
    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001", google_api_key=GOOGLE_API_KEY)
    Chroma.from_documents(
        chunks,
        embeddings,
        persist_directory=str(VECTOR_DB_DIR),
        collection_name="demokart_policy",
    )
    return str(VECTOR_DB_DIR)


if __name__ == "__main__":
    print(ingest_policy())
