from src.data.data_loader import load_table


def get_customer(customer_id: str) -> dict[str, str] | None:
    table = load_table("customers")
    matches = table[table["CustomerID"].str.casefold() == customer_id.strip().casefold()]
    return matches.iloc[0].to_dict() if not matches.empty else None


def get_customer_orders(customer_id: str) -> list[dict[str, str]]:
    table = load_table("orders")
    return table[table["CustomerID"].str.casefold() == customer_id.strip().casefold()].to_dict("records")