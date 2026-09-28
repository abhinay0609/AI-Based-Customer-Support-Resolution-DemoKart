from typing import Any

from src.config.settings import DATA_DIR, OPERATIONAL_DATA_PATH
from src.data.sql_database import execute, initialize_database
from src.models.case_model import CaseUpdate
from src.utils.helpers import today


def _case_database_path():
    return OPERATIONAL_DATA_PATH if OPERATIONAL_DATA_PATH.exists() else DATA_DIR


def create_case(update: CaseUpdate) -> dict[str, Any]:
    initialize_database()
    latest = execute("SELECT CaseID FROM cases ORDER BY rowid DESC LIMIT 1")
    next_number = int(str(latest[0]).replace("CASE", "")) + 1 if latest else 1
    case_id = f"CASE{next_number:03d}"
    record = {"CaseID": case_id, "CustomerID": update.customer_id, "OrderID": update.order_id, "IssueType": update.issue_type, "CaseStatus": update.status, "ResolutionStatus": update.resolution_status, "Priority": update.priority, "Confidence": f"{update.confidence:.2f}", "PendingAction": update.pending_action, "Resolution": update.resolution, "CreatedAt": today(), "UpdatedAt": today()}
    columns = ", ".join(record)
    placeholders = ", ".join("?" for _ in record)
    execute(f"INSERT INTO cases ({columns}) VALUES ({placeholders})", tuple(record.values()))
    return record


def update_case(case_id: str, **changes: Any) -> dict[str, Any] | None:
    initialize_database()
    current = execute("SELECT * FROM cases WHERE upper(CaseID) = upper(?)", (case_id,))
    if not current:
        return None
    aliases = {
        "customer_id": "CustomerID",
        "order_id": "OrderID",
        "issue_type": "IssueType",
        "status": "CaseStatus",
        "resolution_status": "ResolutionStatus",
        "priority": "Priority",
        "confidence": "Confidence",
        "pending_action": "PendingAction",
        "resolution": "Resolution",
    }
    allowed = {"CustomerID", "OrderID", "IssueType", "CaseStatus", "ResolutionStatus", "Priority", "Confidence", "PendingAction", "Resolution"}
    mapped = {aliases.get(key, key): value for key, value in changes.items() if (aliases.get(key, key) in allowed)}
    if mapped:
        assignments = ", ".join(f"{key} = ?" for key in mapped)
        execute(f"UPDATE cases SET {assignments}, UpdatedAt = ? WHERE upper(CaseID) = upper(?)", tuple(mapped.values()) + (today(), case_id))
    updated = execute("SELECT * FROM cases WHERE upper(CaseID) = upper(?)", (case_id,))
    return dict(updated) if updated else None
