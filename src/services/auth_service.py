from src.tools.customer_tools import get_customer

CUSTOMER_PASSWORD = "Demo@123"
SPECIALIST_USERNAME = "amit.support"
SPECIALIST_PASSWORD = "Amit@123"
SPECIALIST_NAME = "Amit"

def authenticate_customer(customer_id: str, password: str) -> dict | None:
    if password != CUSTOMER_PASSWORD:
        return None
    customer = get_customer(customer_id.strip().upper())
    return customer

def authenticate_specialist(username: str, password: str) -> bool:
    return username.strip().casefold() == SPECIALIST_USERNAME.casefold() and password == SPECIALIST_PASSWORD
