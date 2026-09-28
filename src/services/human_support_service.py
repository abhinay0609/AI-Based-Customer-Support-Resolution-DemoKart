from typing import Any

from src.data.sql_database import execute, query_table
from src.models.case_model import CaseUpdate
from src.tools.case_manager import create_case, update_case
from src.utils.helpers import today


def create_human_support_request(state: dict[str, Any]) -> dict[str, Any]:
    case_id = state.get("case_id", "")
    if not case_id:
        case = create_case(CaseUpdate(
            issue_type="Human Support",
            customer_id=state.get("customer_id", ""),
            order_id=state.get("order_id", ""),
            status="Open",
            resolution_status="Pending",
            pending_action="Human review",
            resolution="Human support requested",
            confidence=state.get("understanding_confidence", 0.0),
        ))
        case_id = case["CaseID"]
    existing = execute(
        "SELECT * FROM human_support_requests WHERE CaseID = ? AND Status = 'Pending' ORDER BY RequestID DESC LIMIT 1",
        (case_id,),
    )
    if existing:
        return dict(existing)
    now = today()
    execute(
        """INSERT INTO human_support_requests
        (CaseID, CustomerID, OrderID, Query, RequestType, Status, CreatedAt, UpdatedAt)
        VALUES (?, ?, ?, ?, 'Human Support', 'Pending', ?, ?)""",
        (case_id, state.get("customer_id", ""), state.get("order_id", ""), state.get("query", ""), now, now),
    )
    row = execute(
        "SELECT * FROM human_support_requests WHERE CaseID = ? AND Status = 'Pending' ORDER BY RequestID DESC LIMIT 1",
        (case_id,),
    )
    return dict(row) if row else {"CaseID": case_id, "Status": "Pending"}


def list_pending_human_support_requests() -> list[dict[str, Any]]:
    table = query_table("human_support_requests")
    if table.empty:
        return []
    return table[table["Status"].str.casefold() == "pending"].to_dict("records")


def review_human_support_request(request_id: int, decision: str, reviewer: str, note: str = "") -> dict[str, Any]:
    request = execute("SELECT * FROM human_support_requests WHERE RequestID = ?", (request_id,))
    if not request:
        raise ValueError(f"Human support request {request_id} was not found")
    if request["Status"] != "Pending":
        raise ValueError("This human support request has already been reviewed")
    decision = decision.casefold()
    if decision not in {"approve", "modify", "reject"}:
        raise ValueError("Decision must be approve, modify, or reject")
    status = "Approved" if decision in {"approve", "modify"} else "Rejected"
    execute(
        "UPDATE human_support_requests SET Status = ?, Reviewer = ?, ReviewerNote = ?, UpdatedAt = ? WHERE RequestID = ?",
        (status, reviewer, note, today(), request_id),
    )
    update_case(
        request["CaseID"],
        status="Closed",
        resolution_status="Resolved" if status == "Approved" else "Rejected",
        pending_action="None",
        resolution=f"Human support request {status.casefold()}" + (f": {note}" if note else ""),
    )
    updated = execute("SELECT * FROM human_support_requests WHERE RequestID = ?", (request_id,))
    return dict(updated) if updated else {}