from typing import Any, TypedDict
class WorkflowState(TypedDict,total=False):
    query:str; customer_id:str; case_id:str; order_id:str
    intent:str; secondary_intents:list[str]; entities:dict[str,Any]
    complexity:str; understanding_confidence:float; domain_relevant:bool; guardrail_reason:str
    case_context:dict[str,Any]; case_not_found:bool; case_created:bool
    missing_information:list[str]; plan:dict[str,Any]; current_action:str
    retrieved_documents:str; order_data:dict[str,Any]; tracking_data:list[dict[str,Any]]
    resolution:dict[str,Any]; resolution_confidence:float
    validation_result:dict[str,Any]; escalation_required:bool; escalation_reason:str
    response:str; case_status:str; duplicate_request:bool; duplicate_status:str
    damaged_evidence:dict[str,Any]; audit_log:list[dict[str,Any]]
