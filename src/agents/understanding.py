import json, re
from typing import Any
from pydantic import BaseModel, Field
from src.agents.llm import get_llm

ALLOWED={"general_enquiry","check_refund_policy","track_order","case_follow_up","get_refund",
         "cancel_order","complaint","create_case","damaged_product","contact_human_agent"}
class Understanding(BaseModel):
    primary_intent:str
    secondary_intents:list[str]=Field(default_factory=list)
    entities:dict[str,Any]=Field(default_factory=dict)
    complexity:str
    confidence:float
    missing_information:list[str]=Field(default_factory=list)
    domain_relevant:bool=True
    guardrail_reason:str=""

class UnderstandingAgent:
    def analyze(self,query,customer_id="",order_id="",case_id=""):
        det=self._deterministic(query,customer_id,order_id,case_id)
        if det.primary_intent=="check_refund_policy": return det
        llm=get_llm()
        if not llm: return det
        prompt=f"""You are the intent and safety classifier for DemoKart customer support.
Return ONLY valid JSON with keys: domain_relevant, guardrail_reason, primary_intent, secondary_intents, complexity, confidence.
Allowed intents: {sorted(ALLOWED)}.
Domain means DemoKart customer support: orders, delivery/tracking, returns, refunds, cancellations, complaints, damaged products, cases, policy/FAQ, or requesting a support specialist.
Off-domain examples: travel planning, coding help, politics, recipes, general education, unrelated shopping, weather.
Policy questions about DemoKart returns, refunds, cancellations, delivery and product eligibility are in-domain even when no order ID is supplied.
If off-domain: domain_relevant=false and primary_intent='general_enquiry'.
Do not invent IDs. Confidence must be 0..1.
Customer query: {query}"""
        try:
            raw=llm.invoke(prompt).content
            raw=re.sub(r"^```(?:json)?|```$","",raw.strip()).strip()
            data=json.loads(raw)
            primary=data.get("primary_intent")
            if primary not in ALLOWED: return det
            secondary=[x for x in data.get("secondary_intents",[]) if x in ALLOWED and x!=primary]
            return Understanding(primary_intent=primary,secondary_intents=secondary,entities=det.entities,
                complexity=str(data.get("complexity",det.complexity)).upper(),
                confidence=max(0,min(float(data.get("confidence",det.confidence)),1)),
                missing_information=det.missing_information,
                domain_relevant=bool(data.get("domain_relevant",True)),
                guardrail_reason=str(data.get("guardrail_reason","")))
        except Exception:
            return det

    def _deterministic(self,q,customer_id,order_id,case_id):
        t=q.casefold()
        ents={}
        for key,pat,fallback in [("order_id",r"\bORD\d{4}\b",order_id),("case_id",r"\bCASE\d{3}\b",case_id),("customer_id",r"\bCUST\d{3}\b",customer_id)]:
            m=re.search(pat,q,re.I); ents[key]=m.group(0).upper() if m else fallback
        domain_terms=("order","refund","return","cancel","complaint","damaged","delivery","track","case","support","policy","product","item","arrived","received","replacement","exchange")
        relevant=any(x in t for x in domain_terms)
        intents=[]
        policy_question="policy" in t or "returnable" in t or "how long" in t
        if policy_question:
            intents.append("check_refund_policy")
        else:
            if any(x in t for x in ("human","agent","representative","specialist")): intents.append("contact_human_agent")
            if any(x in t for x in ("case","ticket")): intents.append("case_follow_up")
            if any(x in t for x in ("damaged","broken","cracked","defective")): intents.append("damaged_product"); intents.append("complaint")
            if any(x in t for x in ("refund","money back","reimburse")): intents.append("get_refund")
            if any(x in t for x in ("cancel","cancellation")): intents.append("cancel_order")
            if any(x in t for x in ("where is","track","tracking","delivery status","order status","status of my order")): intents.append("track_order")
            if any(x in t for x in ("complaint","late","delayed","lost","never arrived","wrong item","disappointed")): intents.append("complaint")
            if any(x in t for x in ("create case","open a case","new case")): intents.append("create_case")
        if not intents: intents=["general_enquiry"]
        intents=list(dict.fromkeys(intents))
        needs_order=any(x in intents for x in ("get_refund","cancel_order","track_order","damaged_product"))
        missing=["order_id"] if needs_order and not ents["order_id"] else []
        conf=.93 if intents[0]!="general_enquiry" else (.45 if not relevant else .75)
        return Understanding(primary_intent=intents[0],secondary_intents=intents[1:],entities=ents,
            complexity="COMPLEX" if len(intents)>=3 else ("MEDIUM" if len(intents)==2 else "SIMPLE"),
            confidence=conf,missing_information=missing,domain_relevant=relevant,
            guardrail_reason="" if relevant else "The request is outside DemoKart customer-support scope.")
