from src.data.data_loader import load_table
from src.data.sql_database import execute

def get_order(order_id):
    if not order_id: return None
    table=load_table("orders")
    m=table[table["OrderID"].str.casefold()==order_id.strip().casefold()]
    return m.iloc[0].to_dict() if not m.empty else None

def get_customer_orders(customer_id):
    table=load_table("orders")
    return table[table["CustomerID"].str.casefold()==customer_id.strip().casefold()].to_dict("records")

def update_order_status(order_id,status):
    execute("UPDATE orders SET Status=? WHERE upper(OrderID)=upper(?)",(status,order_id))
