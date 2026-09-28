from src.rag import vectorstore
from src.rag.loader import load_policy_documents


def search_policy(query: str, k: int = 4) -> str:
    try:
        documents = vectorstore.get_vectorstore().similarity_search(query, k=k)
        if documents:
            return "\n\n".join(
                f"[{doc.metadata.get('source')} page {doc.metadata.get('page')}]\n{doc.page_content}"
                for doc in documents
            )
    except Exception:
        pass
    documents = load_policy_documents()
    terms = set(query.lower().split())
    ranked = sorted(documents, key=lambda doc: sum(term in doc.page_content.lower() for term in terms), reverse=True)
    return "\n\n".join(
        f"[{doc.metadata.get('source')} page {doc.metadata.get('page')}]\n{doc.page_content}"
        for doc in ranked[:k]
    )
