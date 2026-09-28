from src.tools.order_tools import get_order, get_customer_orders
from src.tools.tracking_tools import get_tracking_history

class OrderManagementAgent:
    """Agent/tool wrapper for authenticated order operations. Business rules remain deterministic."""
    def get_customer_orders(self, customer_id):
        return get_customer_orders(customer_id)
    def lookup(self, order_id, customer_id):
        order=get_order(order_id)
        if not order or order.get("CustomerID","").casefold()!=customer_id.casefold():
            return None
        return order
    def tracking(self, order_id, customer_id):
        order=self.lookup(order_id,customer_id)
        return get_tracking_history(order_id) if order else []
    def cancellation_eligible(self, order):
        return bool(order and order.get("Status","").casefold() in {"processing","order placed","placed"})
