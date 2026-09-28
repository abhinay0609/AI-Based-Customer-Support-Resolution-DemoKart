from src.data.sql_database import query_table


def get_case(case_id: str) -> dict[str, str] | None:
    table = query_table("cases")
    matches = table[table["CaseID"].str.casefold() == case_id.strip().casefold()]
    return matches.iloc[0].to_dict() if not matches.empty else None


def get_customer_cases(customer_id: str) -> list[dict[str, str]]:
    table = query_table("cases")
    return table[table["CustomerID"].str.casefold() == customer_id.strip().casefold()].to_dict("records")


def get_case_complaints(case_id: str) -> list[dict[str, str]]:
    table = query_table("complaints")
    return table[table["CaseID"].str.casefold() == case_id.strip().casefold()].to_dict("records")