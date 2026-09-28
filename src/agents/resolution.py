from src.tools.refund_rule_engine import evaluate_refund_rules
from src.tools.policy_tools import get_refund_rule
from src.services.refund_approval_service import create_refund_approval,get_latest_refund_approval
from src.tools.order_tools import update_order_status
from src.services.notification_service import notify
from src.tools.case_manager import update_case

def resolve_request(state):
    intents={state.get("intent",""),*state.get("secondary_intents",[])}
    order=state.get("order_data") or {}
    if state.get("duplicate_request"):
        status=state.get("duplicate_status","")
        if status=="Pending":
            return {"resolution":{"status":"Pending","summary":f"A request for order {state.get('order_id')} is already pending under case {state.get('case_id')}. I have not created a duplicate case."},"resolution_confidence":0.99}
        return {"resolution":{"status":"Closed","summary":f"Order {state.get('order_id')} already has a completed refund request under case {state.get('case_id')}. I have not created another case. If you have a new issue, explicitly ask to create a new case."},"resolution_confidence":0.99}
    if "case_follow_up" in intents and state.get("case_context",{}).get("case"):
        c=state["case_context"]["case"]
        return {"resolution":{"status":"Closed" if c.get("CaseStatus")=="Closed" else "Open","summary":f"Case {c.get('CaseID')} is {c.get('CaseStatus','Open')}. Resolution status: {c.get('ResolutionStatus','Pending')}. Current resolution: {c.get('Resolution') or 'None'}."},"resolution_confidence":.98}
    if "track_order" in intents:
        if not order: return {"resolution":{"status":"Open","summary":"I could not verify that order against your customer account."},"resolution_confidence":.95}
        latest=(state.get("tracking_data") or [{}])[-1]
        return {"resolution":{"status":"Resolved","summary":f"Order {order['OrderID']} is {order.get('Status','Unknown')}. Latest tracking: {latest.get('Status','unavailable')} at {latest.get('Location','unavailable')}."},"resolution_confidence":.98}
    if "cancel_order" in intents:
        if not order: return {"resolution":{"status":"Open","summary":"I could not verify that order against your customer account."},"resolution_confidence":.95}
        eligible=order.get("Status","").casefold() in {"processing","order placed","placed"}
        if eligible:
            update_order_status(order["OrderID"],"Cancelled")
            update_case(state.get("case_id",""),status="Closed",resolution_status="Resolved",pending_action="None",resolution="Order cancelled automatically under cancellation rule")
            notify(state.get("customer_id",""),f"Your cancellation request for order {order['OrderID']} has been completed automatically. Case {state.get('case_id')} is closed.",state.get("case_id",""),order["OrderID"])
            return {"resolution":{"status":"Closed","summary":f"Order {order['OrderID']} was eligible for cancellation and has been cancelled automatically. No specialist approval was required."},"resolution_confidence":.98}
        return {"resolution":{"status":"Open","summary":f"Order {order['OrderID']} is currently {order.get('Status')}. It is not eligible for automatic cancellation at this stage, so specialist review is required."},"resolution_confidence":.96}
    if "get_refund" in intents:
        if not order: return {"resolution":{"status":"Open","summary":"I could not verify that order against your customer account."},"resolution_confidence":.95}
        prior=get_latest_refund_approval(order["OrderID"],order.get("CustomerID",""))
        if prior:
            status=prior["Status"]
            if status=="Pending":
                return {"resolution":{"status":"Pending","summary":f"A refund request is already pending for {order['OrderID']} under case {prior['CaseID']}. It has been routed to Support Specialist Amit."},"resolution_confidence":.99}
            outcome="approved" if status=="Approved" else "rejected"
            return {"resolution":{"status":"Closed","summary":f"A previous refund request for {order['OrderID']} was {outcome} under closed case {prior['CaseID']}. No duplicate case was created."},"resolution_confidence":.99}
        rules=evaluate_refund_rules(order,state.get("query",""))
        rule=get_refund_rule(rules.get("condition",""))
        if rule and rule.get("Eligibility") in {"Eligible","Conditional"}:
            approval=create_refund_approval(state.get("case_id",""),order,state.get("query",""))
            return {"resolution":{"status":"Pending","summary":f"Your refund request for {order['OrderID']} has been submitted to Support Specialist Amit for review. Case {state.get('case_id')} is pending.","rule":rule,"refund_approval":approval},"resolution_confidence":.94}
        return {"resolution":{"status":"Escalated","summary":f"Your refund request for {order['OrderID']} requires specialist review because the applicable rule does not allow automatic processing.","rule":rule or rules},"resolution_confidence":.72}
    if "complaint" in intents:
        return {"resolution":{"status":"Open","summary":f"Your complaint for order {order.get('OrderID',state.get('order_id',''))} has been recorded for support follow-up."},"resolution_confidence":.90}
    if state.get("case_created"):
        return {"resolution":{"status":"Open","summary":f"Case {state.get('case_id')} was created and is open for support follow-up."},"resolution_confidence":.94}
    return {"resolution":{"status":"Resolved","summary":"I retrieved the relevant DemoKart information for your request."},"resolution_confidence":.90}
