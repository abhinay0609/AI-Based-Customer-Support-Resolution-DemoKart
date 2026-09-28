from typing import Any

from src.data.data_loader import load_table


def evaluate_refund_rules(order: dict[str, Any] | None, reason: str = "") -> dict[str, Any]:
    if not order:
        return {"eligibility": "Unknown", "action": "Request Information", "reason": "Order information is required"}
    status = str(order.get("Status", "")).strip().lower()
    text = reason.lower()
    if "lost" in status or "not received" in text or "never arrived" in text:
        condition = "Lost in Transit"
    elif "damaged" in text:
        condition = "Damaged Product"
    elif "defect" in text:
        condition = "Defective Product"
    elif "cancel" in status:
        condition = "Cancelled Before Dispatch"
    elif status == "delivered" and not any(word in text for word in ("damaged", "defect", "wrong")):
        condition = "Delivered and No Issue"
    else:
        condition = "Non Returnable Product"
    rules = load_table("refund_rules")
    match = rules[rules["Condition"].str.lower() == condition.lower()]
    if match.empty:
        return {"condition": condition, "eligibility": "Unknown", "action": "Human Review"}
    return {"condition": condition, **match.iloc[0].to_dict()}
