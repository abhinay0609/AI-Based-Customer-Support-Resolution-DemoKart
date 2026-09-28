import json
from src.agents.llm import get_llm
from src.tools.customer_tools import get_customer
from src.utils.prompts import SYSTEM_PROMPT

def generate_response(state):
    fallback=_fallback(state)
    if not state.get("domain_relevant",True): return "Sorry, I can’t help with that because it is outside DemoKart customer-support scope. I can help with orders, delivery/tracking, refunds, returns, cancellations, complaints, damaged products, cases, and DemoKart policies."
    llm=get_llm()
    if not llm: return fallback
    context={k:state.get(k) for k in ("query","intent","secondary_intents","order_data","tracking_data","case_context","resolution","validation_result","case_id","retrieved_documents","duplicate_request","duplicate_status")}
    prompt=f"""{SYSTEM_PROMPT}
Generate only a concise customer-facing response. Use the validated resolution as authoritative.
Never change a business decision. Never invent a case/order ID, refund amount, policy, status, or timeline.
If a request is pending human review, clearly say Support Specialist Amit will review it.
If the request was already completed for the same order, say no duplicate case was created.
If policy context is provided, ground the answer in it.
Context JSON:
{json.dumps(context,default=str)}"""
    try:
        text=llm.invoke(prompt).content.strip()
        return text or fallback
    except Exception:
        return fallback

def _fallback(s):
    if s.get("missing_information"):
        return f"Please provide your {s['missing_information'][0].replace('_',' ')} so I can continue."
    if s.get("resolution",{}).get("summary"): return s["resolution"]["summary"]
    if s.get("retrieved_documents"):
        return "Here is the relevant DemoKart policy information:\n\n" + s["retrieved_documents"][:3500]
    return "I can help with DemoKart orders, policies, refunds, returns, cancellations, complaints, and cases."
