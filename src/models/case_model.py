from typing import Any
from pydantic import BaseModel, Field

class CaseUpdate(BaseModel):
    issue_type: str
    customer_id: str = ""
    order_id: str = ""
    status: str = "Open"
    resolution_status: str = "Pending"
    priority: str = "Medium"
    confidence: float = 0.0
    pending_action: str = "None"
    resolution: str = "None"

class CaseRecord(BaseModel):
    case_id: str
    values: dict[str, Any] = Field(default_factory=dict)
