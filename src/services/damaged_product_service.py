from pathlib import Path
from src.data.sql_database import execute, query_table
from src.tools.case_manager import update_case
from src.services.notification_service import notify
from src.services.refund_approval_service import create_refund_approval
from src.utils.helpers import today

def create_damage_request(case_id, customer_id, order_id, expected_product, evidence_path, evidence_name, uploaded_product, match, damaged, confidence, reason):
    execute("""INSERT INTO damaged_requests
        (CaseID,CustomerID,OrderID,ExpectedProduct,UploadedProduct,EvidencePath,EvidenceName,ProductMatch,DamageDetected,AIConfidence,AIReason,Status,CreatedAt,UpdatedAt)
        VALUES(?,?,?,?,?,?,?,?,?,?,?,'Pending',?,?)""",
        (case_id,customer_id,order_id,expected_product,uploaded_product,evidence_path,evidence_name,match,damaged,float(confidence),reason,today(),today()))
    return get_latest_damage_request(order_id, customer_id)

def get_latest_damage_request(order_id, customer_id=""):
    if customer_id:
        row=execute("""SELECT * FROM damaged_requests WHERE upper(OrderID)=upper(?) AND upper(CustomerID)=upper(?) ORDER BY RequestID DESC LIMIT 1""",(order_id,customer_id))
    else:
        row=execute("SELECT * FROM damaged_requests WHERE upper(OrderID)=upper(?) ORDER BY RequestID DESC LIMIT 1",(order_id,))
    return dict(row) if row else None

def list_pending_damage_requests():
    return query_table("damaged_requests").query("Status.str.casefold() == 'pending'").to_dict("records")

def review_damage_request(request_id, decision, reviewer, note=""):
    row=execute("SELECT * FROM damaged_requests WHERE RequestID=?",(request_id,))
    if not row: raise ValueError("Damage request not found")
    row=dict(row)
    if row["Status"]!="Pending": raise ValueError("This request has already been reviewed")
    d=decision.casefold()
    if d not in {"approve","modify","reject"}: raise ValueError("Invalid decision")

    if d in {"approve","modify"}:
        # Stage 1: Amit approves the evidence/damage. Only now is a separate
        # refund approval request created for Stage 2. The same case remains
        # open until the refund decision is completed.
        damage_status="Approved"
        from src.tools.order_tools import get_order
        order=get_order(row["OrderID"]) or {}
        refund=create_refund_approval(
            row["CaseID"],
            order,
            f"Damaged product evidence approved by {reviewer}. {note}".strip(),
        )
        execute("UPDATE damaged_requests SET Status=?,Reviewer=?,ReviewerNote=?,UpdatedAt=? WHERE RequestID=?",
                (damage_status,reviewer,note,today(),request_id))
        resolution="Damage verification approved. Refund is now pending specialist approval."
        update_case(row["CaseID"],status="Open",resolution_status="Pending",
                    pending_action="Refund approval",resolution=resolution)
        notify(row["CustomerID"],
               f"Damage verification for order {row['OrderID']} was approved. Your refund request is now pending Support Specialist Amit's final approval.",
               row["CaseID"],row["OrderID"])
        return {**dict(execute("SELECT * FROM damaged_requests WHERE RequestID=?",(request_id,))), "RefundApproval": refund}

    # Stage 1 rejection ends the case and creates no refund request.
    execute("UPDATE damaged_requests SET Status='Rejected',Reviewer=?,ReviewerNote=?,UpdatedAt=? WHERE RequestID=?",
            (reviewer,note,today(),request_id))
    resolution="Damaged-product evidence was rejected by the support specialist. No refund request was created."
    update_case(row["CaseID"],status="Closed",resolution_status="Rejected",
                pending_action="None",resolution=resolution)
    notify(row["CustomerID"],
           f"Your damaged-product request for order {row['OrderID']} was rejected after specialist evidence review. No refund request was created.",
           row["CaseID"],row["OrderID"])
    return dict(execute("SELECT * FROM damaged_requests WHERE RequestID=?",(request_id,)))
