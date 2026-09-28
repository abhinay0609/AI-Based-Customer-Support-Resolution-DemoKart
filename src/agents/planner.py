from pydantic import BaseModel,Field
class Plan(BaseModel):
    customer_goal:str
    actions:list[str]=Field(default_factory=list)
    requires_rag:bool=False
    requires_operational_data:bool=False
    human_escalation_possible:bool=False
def create_plan(understanding):
    intents={understanding.primary_intent,*understanding.secondary_intents}
    rag=bool(intents & {"general_enquiry","check_refund_policy","get_refund","cancel_order","damaged_product"})
    data=bool(intents & {"track_order","case_follow_up","get_refund","cancel_order","damaged_product","complaint"})
    actions=["LLM intent/complexity understanding"]
    if rag: actions.append("retrieve policy with RAG")
    if data: actions.append("use authenticated operational tools")
    actions.append("apply deterministic business rules")
    if intents & {"get_refund","damaged_product"}: actions.append("route to human support when required")
    actions.append("LLM response generation")
    return Plan(customer_goal=understanding.primary_intent,actions=actions,requires_rag=rag,requires_operational_data=data,
                human_escalation_possible=bool(intents & {"get_refund","damaged_product"})).model_dump()
