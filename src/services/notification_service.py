from src.data.sql_database import execute, query_table
from src.utils.helpers import today

def notify(customer_id, message, case_id="", order_id=""):
    execute(
        """INSERT INTO notifications(CustomerID, CaseID, OrderID, Message, IsRead, CreatedAt)
           VALUES(?,?,?,?,0,?)""",
        (customer_id, case_id, order_id, message, today()),
    )

def get_notifications(customer_id, unread_only=False):
    query = "SELECT * FROM notifications WHERE upper(CustomerID)=upper(?)"
    params = [customer_id]
    if unread_only:
        query += " AND IsRead=0"
    query += " ORDER BY NotificationID DESC"
    return query_table("notifications").query("CustomerID.str.casefold() == @customer_id.casefold()", local_dict={"customer_id": customer_id}).to_dict("records") if not unread_only else query_table("notifications").query("CustomerID.str.casefold() == @customer_id.casefold() and IsRead == 0", local_dict={"customer_id": customer_id}).to_dict("records")

def mark_read(notification_id, customer_id):
    execute("UPDATE notifications SET IsRead=1 WHERE NotificationID=? AND upper(CustomerID)=upper(?)", (notification_id, customer_id))
