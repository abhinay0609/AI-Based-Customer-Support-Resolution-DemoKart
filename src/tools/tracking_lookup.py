from typing import Any
import pandas as pd
from src.config.settings import DATA_DIR


def get_tracking_history(order_id: str) -> list[dict[str, Any]]:
    if not order_id:
        return []
    frame = pd.read_csv(DATA_DIR / "tracking.csv", dtype=str).fillna("")
    rows = frame[frame["OrderID"].str.upper() == order_id.upper()].copy()
    rows = rows.sort_values("TrackingDate", ascending=False)
    return rows.to_dict(orient="records")
