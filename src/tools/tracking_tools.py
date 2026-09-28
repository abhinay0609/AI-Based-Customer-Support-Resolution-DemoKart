from src.data.data_loader import load_table


def get_tracking_history(order_id: str) -> list[dict[str, str]]:
    table = load_table("tracking")
    matches = table[table["OrderID"].str.casefold() == order_id.strip().casefold()]
    if "TrackingDate" in matches.columns:
        matches = matches.sort_values("TrackingDate")
    return matches.to_dict("records")


def get_latest_tracking_status(order_id: str) -> dict[str, str] | None:
    history = get_tracking_history(order_id)
    return history[-1] if history else None