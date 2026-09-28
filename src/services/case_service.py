from typing import Any

from src.models.case_model import CaseUpdate
from src.tools.case_manager import create_case
from src.tools.case_tools import get_case, get_case_complaints, get_customer_cases


def retrieve_case_context(customer_id: str = "", case_id: str = "", order_id: str = "") -> dict[str, Any]:
    case = get_case(case_id) if case_id else None
    if not case and not case_id and customer_id:
        cases = get_customer_cases(customer_id)
        case = next((item for item in reversed(cases) if not order_id or item.get("OrderID") == order_id), None)
    if not case:
        return {}
    return {"case": case, "complaints": get_case_complaints(case.get("CaseID", ""))}


def create_runtime_case(state: dict) -> dict[str, Any]:
    context = state.get("case_context") or {}
    if context.get("case"):
        return context["case"]
    intents = {state.get("intent", ""), *state.get("secondary_intents", [])}
    issue_type = "Complaint" if "complaint" in intents else "Support Request"
    if "get_refund" in intents:
        issue_type = "Refund Request"
    if "cancel_order" in intents:
        issue_type = "Cancellation"
    return create_case(CaseUpdate(
        issue_type=issue_type,
        customer_id=state.get("customer_id", ""),
        order_id=state.get("order_id", ""),
        pending_action="Support review",
        resolution="None",
        confidence=state.get("understanding_confidence", 0.0),
    )).copy()