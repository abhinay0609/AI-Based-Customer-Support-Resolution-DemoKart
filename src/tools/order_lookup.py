from typing import Any
import pandas as pd
from src.config.settings import DATA_DIR


def get_order_details(order_id: str) -> dict[str, Any] | None:
    if not order_id:
        return None
    frame = pd.read_csv(DATA_DIR / "orders.csv", dtype=str).fillna("")
    rows = frame[frame["OrderID"].str.upper() == order_id.upper()]
    return rows.iloc[0].to_dict() if not rows.empty else None
