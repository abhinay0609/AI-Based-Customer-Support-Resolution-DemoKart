from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter


def split_policy_documents(documents: list[Document]) -> list[Document]:
    splitter = RecursiveCharacterTextSplitter(chunk_size=1100, chunk_overlap=160)
    return splitter.split_documents(documents)