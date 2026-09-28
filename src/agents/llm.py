from src.config.settings import GEMINI_MODEL, GOOGLE_API_KEY, TEMPERATURE


def get_llm():
    if not GOOGLE_API_KEY:
        return None
    from langchain_google_genai import ChatGoogleGenerativeAI
    return ChatGoogleGenerativeAI(
        model=GEMINI_MODEL,
        temperature=TEMPERATURE,
        google_api_key=GOOGLE_API_KEY,
    )