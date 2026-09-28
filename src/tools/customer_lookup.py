from typing import Any
import pandas as pd
from src.config.settings import DATA_DIR


def get_customer_details(customer_id: str) -> dict[str, Any] | None:
    if not customer_id:
        return None
    frame = pd.read_csv(DATA_DIR / "customers.csv", dtype=str).fillna("")
    rows = frame[frame["CustomerID"].str.upper() == customer_id.upper()]
    return rows.iloc[0].to_dict() if not rows.empty else None
