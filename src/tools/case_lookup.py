from typing import Any
import pandas as pd
from src.config.settings import DATA_DIR


def get_case_details(case_id: str) -> dict[str, Any] | None:
    if not case_id:
        return None
    frame = pd.read_csv(DATA_DIR / "cases.csv", dtype=str).fillna("")
    rows = frame[frame["CaseID"].str.upper() == case_id.upper()]
    return rows.iloc[0].to_dict() if not rows.empty else None
