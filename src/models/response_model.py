from typing import Any
from pydantic import BaseModel, Field

class SupportResponse(BaseModel):
    intent: str
    entities: dict[str, Any] = Field(default_factory=dict)
    tools_used: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0, le=1)
    resolution_status: str
    case_id: str = ""
    response: str
    escalated: bool = False
    case_information: dict[str, Any] = Field(default_factory=dict)
