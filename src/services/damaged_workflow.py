from pathlib import Path
from src.agents.vision_agent import DamageAssessmentAgent
from src.data.sql_database import execute
from src.models.case_model import CaseUpdate
from src.tools.case_manager import create_case
from src.services.damaged_product_service import create_damage_request,get_latest_damage_request
from src.services.notification_service import notify
from src.utils.helpers import today
from src.config.settings import DATA_DIR


def process_damage_upload(customer_id, order, uploaded_file):
    existing=get_latest_damage_request(order["OrderID"],customer_id)
    if existing and existing["Status"]=="Pending":
        return {"duplicate":True,"request":existing,
                "message":f"A damaged-product request for {order['OrderID']} is already pending under case {existing['CaseID']}."}

    case=create_case(CaseUpdate(
        issue_type="Damaged Product", customer_id=customer_id, order_id=order["OrderID"],
        status="Open", resolution_status="Pending", priority="High",
        pending_action="Evidence analysis", resolution="Waiting for product-evidence analysis"))

    evidence_dir=DATA_DIR/"evidence"
    evidence_dir.mkdir(parents=True,exist_ok=True)
    safe_name=f"{case['CaseID']}_{Path(uploaded_file.name).name.replace(' ','_')}"
    path=evidence_dir/safe_name
    with open(path,"wb") as f:
        f.write(uploaded_file.getbuffer())

    assessment=DamageAssessmentAgent().assess(
        str(path), order.get("Product",""), order.get("ProductCategory","")
    )
    match=assessment.get("product_match","UNCERTAIN")
    damaged=assessment.get("damaged","UNCERTAIN")
    confidence=float(assessment.get("confidence",0) or 0)
    reason=assessment.get("reason","")

    # Only a confirmed match + visible damage goes straight to the specialist queue.
    # A product mismatch is also sent to a human because it is a high-risk evidence issue.
    if match=="MATCH" and damaged=="YES":
        status="Pending"
        summary="Product match confirmed and visible damage detected. Pending specialist approval."
        pending_action="Human review"
        notify(customer_id,
               f"Damage evidence for order {order['OrderID']} was received and sent to Support Specialist Amit for review.",
               case["CaseID"],order["OrderID"])
    elif match=="MISMATCH":
        status="Pending"
        summary="Product mismatch flagged. Specialist review is required before any return/refund decision."
        pending_action="Human review - product mismatch"
        notify(customer_id,
               f"The uploaded evidence for order {order['OrderID']} does not appear to match the ordered product. Amit will review it.",
               case["CaseID"],order["OrderID"])
    elif damaged=="NO":
        status="Closed"
        summary="The uploaded product appears undamaged, so no return or refund is initiated."
        pending_action="None"
        execute("UPDATE cases SET CaseStatus='Closed',ResolutionStatus='Resolved',PendingAction='None',Resolution=?,UpdatedAt=? WHERE CaseID=?",
                (summary,today(),case["CaseID"]))
    else:
        # Unclear model output should not cause an automatic refund.
        status="Pending"
        summary="The evidence could not be assessed confidently. Specialist review is required."
        pending_action="Human review - low confidence"
        notify(customer_id,
               f"The image for order {order['OrderID']} could not be assessed confidently. Amit will review the evidence.",
               case["CaseID"],order["OrderID"])

    req=create_damage_request(
        case["CaseID"],customer_id,order["OrderID"],order.get("Product",""),
        str(path),path.name,assessment.get("uploaded_product",""),match,damaged,confidence,reason
    )
    execute("UPDATE cases SET PendingAction=?, Resolution=?, UpdatedAt=? WHERE CaseID=?",
            (pending_action,summary,today(),case["CaseID"]))
    return {"duplicate":False,"case":case,"request":req,"assessment":assessment,"summary":summary}
