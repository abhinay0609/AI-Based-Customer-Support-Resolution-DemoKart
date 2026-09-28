from pathlib import Path
from typing import Final

import pandas as pd

from src.config.settings import DATA_DIR, OPERATIONAL_DATA_PATH
from src.data.sql_database import query_table


class DataAccessError(RuntimeError):
    """Raised when an operational data source cannot be safely read."""


REQUIRED_COLUMNS: Final[dict[str, tuple[str, ...]]] = {
    "customers": ("CustomerID", "CustomerName", "Email", "Phone"),
    "orders": ("OrderID", "CustomerID", "Product", "ProductCategory", "Status"),
    "tracking": ("OrderID", "TrackingDate", "Location", "Status"),
    "cases": ("CaseID", "CustomerID", "OrderID", "CaseStatus", "ResolutionStatus"),
    "complaints": ("ComplaintID", "CaseID", "CustomerID", "OrderID"),
    "refund_rules": ("RuleID", "Condition", "Eligibility", "Action"),
}


def _data_path() -> Path:
    operational = OPERATIONAL_DATA_PATH
    return operational if operational.exists() else DATA_DIR


def load_table(name: str) -> pd.DataFrame:
    if name not in REQUIRED_COLUMNS:
        raise DataAccessError(f"Unknown operational table: {name}")
    try:
        table = query_table(name)
    except Exception as exc:
        raise DataAccessError(f"Could not read SQL table {name}: {exc}") from exc
    missing = set(REQUIRED_COLUMNS[name]) - set(table.columns)
    if missing:
        raise DataAccessError(f"SQL table {name} is missing columns: {sorted(missing)}")
    return table


def find_by_id(table_name: str, column: str, value: str) -> dict[str, str] | None:
    if not value or not isinstance(value, str):
        return None
    table = load_table(table_name)
    if column not in table.columns:
        raise DataAccessError(f"{table_name}.csv has no {column} column")
    matches = table[table[column].str.casefold() == value.strip().casefold()]
    return matches.iloc[0].to_dict() if not matches.empty else None