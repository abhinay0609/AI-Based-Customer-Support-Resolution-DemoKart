import sqlite3
from pathlib import Path
import pandas as pd
from src.config.settings import DATA_DIR, OPERATIONAL_DATA_PATH

TABLES = ("customers", "orders", "tracking", "cases", "complaints", "refund_rules")

def database_path() -> Path:
    base = OPERATIONAL_DATA_PATH if OPERATIONAL_DATA_PATH.exists() else DATA_DIR
    base.mkdir(parents=True, exist_ok=True)
    return base / "operational.db"

def _connect():
    connection = sqlite3.connect(database_path(), check_same_thread=False)
    connection.row_factory = sqlite3.Row
    return connection

def _seed_csv_tables(connection):
    base = OPERATIONAL_DATA_PATH if OPERATIONAL_DATA_PATH.exists() else DATA_DIR
    for table_name in TABLES:
        csv_path = base / f"{table_name}.csv"
        if csv_path.exists():
            pd.read_csv(csv_path, dtype=str).fillna("").to_sql(
                table_name, connection, if_exists="replace", index=False
            )

def initialize_database(force: bool = False):
    with _connect() as connection:
        existing = connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='orders'"
        ).fetchone()
        if force or not existing:
            _seed_csv_tables(connection)

        connection.execute("""CREATE TABLE IF NOT EXISTS refund_approvals (
            ApprovalID INTEGER PRIMARY KEY AUTOINCREMENT,
            CaseID TEXT NOT NULL, CustomerID TEXT, OrderID TEXT,
            RequestedAmount REAL NOT NULL, ApprovedAmount REAL,
            Reason TEXT NOT NULL, Status TEXT NOT NULL DEFAULT 'Pending',
            Reviewer TEXT, ReviewerNote TEXT, CreatedAt TEXT NOT NULL, UpdatedAt TEXT NOT NULL
        )""")
        connection.execute("CREATE INDEX IF NOT EXISTS idx_approvals_order ON refund_approvals(CustomerID, OrderID)")
        connection.execute("CREATE INDEX IF NOT EXISTS idx_approvals_status ON refund_approvals(Status)")

        connection.execute("""CREATE TABLE IF NOT EXISTS damaged_requests (
            RequestID INTEGER PRIMARY KEY AUTOINCREMENT,
            CaseID TEXT NOT NULL, CustomerID TEXT NOT NULL, OrderID TEXT NOT NULL,
            ExpectedProduct TEXT NOT NULL, UploadedProduct TEXT,
            EvidencePath TEXT NOT NULL, EvidenceName TEXT NOT NULL,
            ProductMatch TEXT NOT NULL DEFAULT 'Unknown',
            DamageDetected TEXT NOT NULL DEFAULT 'Unknown',
            AIConfidence REAL DEFAULT 0,
            AIReason TEXT, Status TEXT NOT NULL DEFAULT 'Pending',
            Reviewer TEXT, ReviewerNote TEXT, CreatedAt TEXT NOT NULL, UpdatedAt TEXT NOT NULL
        )""")
        connection.execute("CREATE INDEX IF NOT EXISTS idx_damage_order ON damaged_requests(CustomerID, OrderID)")
        connection.execute("CREATE INDEX IF NOT EXISTS idx_damage_status ON damaged_requests(Status)")

        connection.execute("""CREATE TABLE IF NOT EXISTS notifications (
            NotificationID INTEGER PRIMARY KEY AUTOINCREMENT,
            CustomerID TEXT NOT NULL, CaseID TEXT, OrderID TEXT,
            Message TEXT NOT NULL, IsRead INTEGER NOT NULL DEFAULT 0,
            CreatedAt TEXT NOT NULL
        )""")
        connection.execute("CREATE INDEX IF NOT EXISTS idx_notifications_customer ON notifications(CustomerID, IsRead)")

        connection.execute("""CREATE TABLE IF NOT EXISTS audit_events (
            AuditID INTEGER PRIMARY KEY AUTOINCREMENT,
            EventType TEXT NOT NULL, Actor TEXT, CaseID TEXT, OrderID TEXT,
            Payload TEXT, CreatedAt TEXT NOT NULL
        )""")

        connection.commit()
    return database_path()

def query_table(table_name: str) -> pd.DataFrame:
    initialize_database()
    with _connect() as connection:
        return pd.read_sql_query(f'SELECT * FROM "{table_name}"', connection).fillna("")

def execute(query: str, parameters: tuple = ()):
    initialize_database()
    with _connect() as connection:
        cur = connection.execute(query, parameters)
        connection.commit()
        return cur.fetchone()

def execute_many(query: str, parameters: list[tuple]):
    initialize_database()
    with _connect() as connection:
        connection.executemany(query, parameters)
        connection.commit()
