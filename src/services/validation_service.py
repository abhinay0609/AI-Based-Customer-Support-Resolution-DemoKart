from pydantic import BaseModel,Field
from src.config.settings import RESOLUTION_THRESHOLD
class ValidationResult(BaseModel):
    result:str
    reasons:list[str]=Field(default_factory=list)
def validate_resolution(state):
    reasons=[]
    if not state.get("domain_relevant",True): reasons.append("request blocked by domain guardrail")
    if state.get("missing_information"): reasons.append("required information is missing")
    if state.get("plan",{}).get("requires_rag") and not state.get("retrieved_documents") and state.get("intent") in {"check_refund_policy","general_enquiry"}:
        reasons.append("policy context was not retrieved")
    if state.get("resolution") and state.get("resolution_confidence",0)<RESOLUTION_THRESHOLD and state.get("intent") not in {"general_enquiry","check_refund_policy"}:
        reasons.append("resolution confidence is below threshold")
    return ValidationResult(result="FAIL" if reasons else "PASS",reasons=reasons)
