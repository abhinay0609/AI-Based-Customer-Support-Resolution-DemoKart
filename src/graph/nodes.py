from datetime import datetime,timezone
from src.agents.understanding import UnderstandingAgent
from src.agents.planner import create_plan
from src.agents.order_management import OrderManagementAgent
from src.agents.response import generate_response
from src.services.case_service import retrieve_case_context,create_runtime_case
from src.services.refund_approval_service import get_latest_refund_approval,create_refund_approval
from src.services.damaged_product_service import get_latest_damage_request,create_damage_request
from src.services.validation_service import validate_resolution
from src.tools.case_manager import create_case
from src.models.case_model import CaseUpdate
from src.rag.retriever import search_policy
from src.agents.resolution import resolve_request
from src.utils.logger import audit_event

def preprocess(s): return {"query":s.get("query","").strip(),"audit_log":[{"node":"preprocess"}]}

def understand_query(s):
    u=UnderstandingAgent().analyze(s["query"],s.get("customer_id",""),s.get("order_id",""),s.get("case_id",""))
    return {"intent":u.primary_intent,"secondary_intents":u.secondary_intents,"entities":u.entities,"order_id":u.entities["order_id"],"case_id":u.entities["case_id"],"customer_id":u.entities["customer_id"],
            "complexity":u.complexity,"understanding_confidence":u.confidence,"missing_information":u.missing_information,
            "domain_relevant":u.domain_relevant,"guardrail_reason":u.guardrail_reason,"audit_log":[{"node":"understanding_agent"}]}

def guardrail_node(s):
    if not s.get("domain_relevant",True):
        return {
            "current_action":"guardrail",
            "case_created": False,
            "duplicate_request": False,
            "escalation_required": False,
            "response":"Sorry, I can’t help with that because it is outside DemoKart customer-support scope. I can help with orders, delivery/tracking, refunds, returns, cancellations, complaints, damaged products, cases, and DemoKart policies.",
            "audit_log":[{"node":"guardrail","decision":"BLOCK"}],
        }
    return {"current_action":"continue","audit_log":[{"node":"guardrail","decision":"ALLOW"}]}

def retrieve_case_context_node(s):
    ctx=retrieve_case_context(s.get("customer_id",""),s.get("case_id",""),s.get("order_id",""))
    return {"case_context":ctx,"case_not_found":bool(s.get("case_id")) and "case" in s.get("intent","") and not ctx,"audit_log":[{"node":"case_context_retrieval"}]}

def create_or_update_case(s):
    intents={s.get("intent",""),*s.get("secondary_intents",[])}
    transactional=intents & {"get_refund","cancel_order","complaint","create_case","damaged_product"}
    if not transactional: return {"case_created":False,"audit_log":[{"node":"case_management","action":"NO_CASE"}]}
    # Never create a second refund/damage case for the same order unless explicitly asking for a new case.
    explicit_new=any(x in s["query"].casefold() for x in ("new case","create a new case","open a new case"))
    order_id=s.get("order_id",""); cust=s.get("customer_id","")
    if "get_refund" in intents and order_id and not explicit_new:
        prior=get_latest_refund_approval(order_id,cust)
        if prior:
            return {"case_id":prior["CaseID"],"case_status":"Closed" if prior["Status"]!="Pending" else "Open","case_created":False,
                    "duplicate_request":True,"duplicate_status":prior["Status"],"audit_log":[{"node":"case_management","action":"DUPLICATE_REFUND","existing_case":prior["CaseID"]}]}
    if "damaged_product" in intents and order_id and not explicit_new:
        prior=get_latest_damage_request(order_id,cust)
        if prior:
            return {"case_id":prior["CaseID"],"case_status":"Closed" if prior["Status"]!="Pending" else "Open","case_created":False,
                    "duplicate_request":True,"duplicate_status":prior["Status"],"audit_log":[{"node":"case_management","action":"DUPLICATE_DAMAGE","existing_case":prior["CaseID"]}]}
    case=s.get("case_context",{}).get("case") if s.get("case_context") else None
    if not case: case=create_runtime_case(s)
    return {"case_id":case.get("CaseID",""),"case_status":case.get("CaseStatus","Open"),"case_created":True,"audit_log":[{"node":"case_management","action":"CREATE"}]}

def check_information(s):
    return {"current_action":"missing_information" if s.get("missing_information") else "continue","audit_log":[{"node":"information_check"}]}

def planner_node(s):
    obj=type("U",(),{"primary_intent":s["intent"],"secondary_intents":s.get("secondary_intents",[]),"complexity":s.get("complexity","SIMPLE")})()
    return {"plan":create_plan(obj),"audit_log":[{"node":"planner"}]}

def router_node(s):
    intents={s.get("intent",""),*s.get("secondary_intents",[])}
    if "guardrail"==s.get("current_action"): return {"current_action":"guardrail"}
    if "check_refund_policy" in intents or "general_enquiry" in intents: return {"current_action":"rag"}
    if "track_order" in intents: return {"current_action":"tracking_lookup"}
    if intents & {"get_refund","cancel_order","complaint","damaged_product"}: return {"current_action":"order_lookup"}
    return {"current_action":"resolution"}

def rag_node(s): return {"retrieved_documents":search_policy(s["query"]),"audit_log":[{"node":"policy_rag"}]}

def order_lookup_node(s):
    agent=OrderManagementAgent(); order=agent.lookup(s.get("order_id",""),s.get("customer_id",""))
    return {"order_data":order or {},"audit_log":[{"node":"order_management_agent","action":"lookup"}]}

def tracking_lookup_node(s):
    agent=OrderManagementAgent()
    return {"order_data":agent.lookup(s.get("order_id",""),s.get("customer_id","")) or {},"tracking_data":agent.tracking(s.get("order_id",""),s.get("customer_id","")),"audit_log":[{"node":"order_management_agent","action":"tracking"}]}

def resolution_node(s):
    return {**resolve_request(s),"audit_log":[{"node":"resolution_agent"}]}

def validation_node(s):
    r=validate_resolution(s)
    return {"validation_result":r.model_dump(),"escalation_required":r.result=="FAIL","escalation_reason":"; ".join(r.reasons),"audit_log":[{"node":"validation"}]}

def human_escalation_node(s): return {"escalation_required":True,"case_status":"Open","audit_log":[{"node":"human_support_agent","reason":s.get("escalation_reason","Human review required")}]}

def response_generation_node(s): return {"response":generate_response(s),"audit_log":[{"node":"LLM_response"}]}

def case_closure_node(s):
    # Pending human cases remain Open; closed only after specialist action.
    if s.get("escalation_required") or s.get("resolution",{}).get("status") in {"Pending","Escalated"}:
        return {"case_status":"Open","audit_log":[{"node":"case_closure","action":"WAIT_FOR_HUMAN"}]}
    return {"case_status":"Closed" if s.get("resolution",{}).get("status")=="Closed" else s.get("resolution",{}).get("status","Resolved"),
            "audit_log":[{"node":"case_closure"}]}

def audit_logging_node(s):
    audit_event("workflow_execution",{"query":s.get("query"),"intent":s.get("intent"),"case_id":s.get("case_id"),"order_id":s.get("order_id"),
                                     "validation":s.get("validation_result"),"escalation":s.get("escalation_required",False)})
    return {"audit_log":[{"timestamp":datetime.now(timezone.utc).isoformat(),"node":"audit"}]}
