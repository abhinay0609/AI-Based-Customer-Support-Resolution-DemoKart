"""Fresh-demo startup helpers.

The application intentionally does NOT seed pending human-review requests.
Refund and damaged-product queues are populated only by real customer actions
performed during the current demo/session.
"""
from src.data.sql_database import initialize_database


def seed_demo_cases():
    """Initialize the local database without creating synthetic support requests."""
    initialize_database(force=True)
