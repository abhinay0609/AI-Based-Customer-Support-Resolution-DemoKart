import logging
import json
from datetime import datetime, timezone
from typing import Any
from src.config.settings import LOG_LEVEL, LOG_PATH

def get_logger(name: str) -> logging.Logger:
    logging.basicConfig(level=getattr(logging, LOG_LEVEL.upper(), logging.INFO), format="%(asctime)s %(levelname)s %(name)s %(message)s")
    return logging.getLogger(name)


def audit_event(event: str, payload: dict[str, Any]) -> None:
    record = {"timestamp": datetime.now(timezone.utc).isoformat(), "event": event, "payload": payload}
    with (LOG_PATH / "audit.log.jsonl").open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, default=str) + "\n")
