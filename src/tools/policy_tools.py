from src.data.data_loader import load_table


def get_refund_rule(condition: str) -> dict[str, str] | None:
    table = load_table("refund_rules")
    matches = table[table["Condition"].str.casefold() == condition.strip().casefold()]
    return matches.iloc[0].to_dict() if not matches.empty else None