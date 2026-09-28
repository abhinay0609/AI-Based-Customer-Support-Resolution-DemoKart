import hashlib
import json

from langchain_chroma import Chroma

from src.config.settings import VECTORSTORE_PATH
from src.rag.embeddings import get_embeddings
from src.rag.loader import load_policy_documents, policy_paths
from src.rag.splitter import split_policy_documents

COLLECTION_NAME = "demokart_policy"
MANIFEST_PATH = VECTORSTORE_PATH / "manifest.json"


def _fingerprint() -> str:
    digest = hashlib.sha256()
    for path in policy_paths():
        digest.update(path.name.encode())
        digest.update(str(path.stat().st_mtime_ns).encode())
        digest.update(str(path.stat().st_size).encode())
    return digest.hexdigest()


def initialize_rag(force: bool = False) -> Chroma:
    fingerprint = _fingerprint()
    current = {}
    if MANIFEST_PATH.exists():
        current = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    embeddings = get_embeddings()
    if force or current.get("fingerprint") != fingerprint:
        documents = split_policy_documents(load_policy_documents())
        try:
            Chroma(
                embedding_function=embeddings,
                persist_directory=str(VECTORSTORE_PATH),
                collection_name=COLLECTION_NAME,
            ).delete_collection()
        except Exception:
            pass
        store = Chroma.from_documents(
            documents,
            embeddings,
            persist_directory=str(VECTORSTORE_PATH),
            collection_name=COLLECTION_NAME,
        )
        MANIFEST_PATH.write_text(json.dumps({"fingerprint": fingerprint}), encoding="utf-8")
        return store
    return Chroma(embedding_function=embeddings, persist_directory=str(VECTORSTORE_PATH), collection_name=COLLECTION_NAME)


def get_vectorstore():
    return initialize_rag()
