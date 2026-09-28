from typing import Any
import pandas as pd
from src.config.settings import DATA_DIR
from src.utils.helpers import today


def add_complaint(case_id: str, customer_id: str, order_id: str, complaint_type: str, description: str, severity: str = "Medium") -> dict[str, Any]:
    path = DATA_DIR / "complaints.csv"
    frame = pd.read_csv(path, dtype=str).fillna("")
    next_number = len(frame) + 1
    record = {"ComplaintID": f"COMP{next_number:03d}", "CaseID": case_id, "CustomerID": customer_id, "OrderID": order_id, "ComplaintType": complaint_type, "Description": description, "Severity": severity, "Status": "Open", "CreatedAt": today()}
    frame = pd.concat([frame, pd.DataFrame([record])], ignore_index=True)
    frame.to_csv(path, index=False)
    return record
