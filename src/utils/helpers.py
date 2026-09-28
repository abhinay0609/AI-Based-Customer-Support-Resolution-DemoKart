import re
from datetime import date
from typing import Any

ORDER_PATTERN = re.compile(r"\bORD\d{4}\b", re.IGNORECASE)
CASE_PATTERN = re.compile(r"\bCASE\d{3}\b", re.IGNORECASE)

def extract_entities(query: str) -> dict[str, Any]:
    order = ORDER_PATTERN.search(query)
    case = CASE_PATTERN.search(query)
    return {"order_id": order.group(0).upper() if order else "", "case_id": case.group(0).upper() if case else ""}

def today() -> str:
    return date.today().isoformat()

def clean(value: Any) -> Any:
    return "" if value is None else value
