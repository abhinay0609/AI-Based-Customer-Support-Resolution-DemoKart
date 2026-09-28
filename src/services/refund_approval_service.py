from src.data.sql_database import execute, query_table
from src.tools.case_manager import update_case
from src.services.notification_service import notify
from src.utils.helpers import today

def get_latest_refund_approval(order_id, customer_id=""):
    if not order_id:
        return None
    if customer_id:
        row = execute("""SELECT * FROM refund_approvals
                         WHERE upper(OrderID)=upper(?) AND upper(CustomerID)=upper(?)
                         ORDER BY ApprovalID DESC LIMIT 1""", (order_id, customer_id))
    else:
        row = execute("SELECT * FROM refund_approvals WHERE upper(OrderID)=upper(?) ORDER BY ApprovalID DESC LIMIT 1", (order_id,))
    return dict(row) if row else None

def list_pending_refund_approvals():
    return query_table("refund_approvals").query("Status.str.casefold() == 'pending'").to_dict("records")

def create_refund_approval(case_id, order, reason):
    existing = get_latest_refund_approval(order.get("OrderID",""), order.get("CustomerID",""))
    if existing:
        return existing
    now=today()
    execute("""INSERT INTO refund_approvals
        (CaseID,CustomerID,OrderID,RequestedAmount,Reason,Status,CreatedAt,UpdatedAt)
        VALUES(?,?,?,?,?,'Pending',?,?)""",
        (case_id, order.get("CustomerID",""), order.get("OrderID",""),
         float(order.get("Amount") or 0), reason, now, now))
    row=execute("SELECT * FROM refund_approvals WHERE CaseID=? ORDER BY ApprovalID DESC LIMIT 1",(case_id,))
    return dict(row) if row else {}

def review_refund_approval(approval_id, decision, reviewer, approved_amount=None, note=""):
    approval=execute("SELECT * FROM refund_approvals WHERE ApprovalID=?",(approval_id,))
    if not approval: raise ValueError("Refund request not found")
    approval=dict(approval)
    if approval["Status"]!="Pending": raise ValueError("This refund request has already been reviewed")
    decision=decision.casefold()
    requested=float(approval["RequestedAmount"])
    if decision=="approve":
        status="Approved"; amount=requested
    elif decision=="modify":
        if approved_amount is None or not 0 <= float(approved_amount) <= requested:
            raise ValueError("Modified amount must be between 0 and requested amount")
        status="Approved"; amount=float(approved_amount)
    elif decision=="reject":
        status="Rejected"; amount=None
    else:
        raise ValueError("Decision must be approve, modify, or reject")
    execute("""UPDATE refund_approvals SET Status=?,ApprovedAmount=?,Reviewer=?,ReviewerNote=?,UpdatedAt=?
               WHERE ApprovalID=?""",(status,amount,reviewer,note,today(),approval_id))
    resolution = f"Refund approved for {amount:g}" if status=="Approved" else "Refund rejected"
    update_case(approval["CaseID"], status="Closed", resolution_status="Resolved" if status=="Approved" else "Rejected",
                pending_action="None", resolution=resolution)
    msg = (f"Your case {approval['CaseID']} for order {approval['OrderID']} has been closed. "
           + (f"Your refund of {amount:g} has been initiated." if status=="Approved" else "Your refund request was rejected after specialist review."))
    notify(approval["CustomerID"], msg, approval["CaseID"], approval["OrderID"])
    return dict(execute("SELECT * FROM refund_approvals WHERE ApprovalID=?",(approval_id,)))

def seed_pending_refunds():
    """Deprecated compatibility hook: never seed specialist requests."""
    return None
