import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.data.sql_database import initialize_database, query_table
from src.graph.workflow import run_workflow
from src.services.refund_approval_service import list_pending_refund_approvals, review_refund_approval


@pytest.fixture(autouse=True)
def clean_runtime():
    db = ROOT / "data" / "operational.db"
    if db.exists():
        db.unlink()
    initialize_database(force=True)
    yield


def test_t1_general_enquiry_uses_policy_rag():
    result = run_workflow("What is your refund policy?", "CUST001")
    assert result["domain_relevant"] is True
    assert result["intent"] in {"check_refund_policy", "general_enquiry"}
    assert result["retrieved_documents"]
    assert result["case_created"] is False


@pytest.mark.parametrize("query", [
    "What is the refund policy?",
    "What is the return policy?",
    "What is the cancellation policy?",
])
def test_policy_questions_use_rag_without_human_review(query):
    result = run_workflow(query, "CUST001")
    assert result["intent"] == "check_refund_policy"
    assert result["retrieved_documents"]
    assert result["case_created"] is False
    assert result["escalation_required"] is False
    assert "pending human review" not in result["response"].casefold()


def test_t2_order_lookup_is_authenticated():
    result = run_workflow("What is the current status of my order ORD1002?", "CUST001")
    assert result["intent"] == "track_order"
    assert result["order_data"]["OrderID"] == "ORD1002"
    assert result["order_data"]["CustomerID"] == "CUST001"
    assert "ORD1002" in result["response"]


def test_t3_refund_creates_only_pending_human_request():
    result = run_workflow("My order ORD1003 never arrived. I want a refund.", "CUST002")
    assert result["order_data"]["OrderID"] == "ORD1003"
    assert result["case_created"] is True
    assert result["resolution"]["status"] == "Pending"
    pending = list_pending_refund_approvals()
    assert len(pending) == 1
    assert pending[0]["CustomerID"] == "CUST002"
    assert pending[0]["OrderID"] == "ORD1003"


def test_refund_duplicate_is_not_created_after_approval():
    first = run_workflow("My order ORD1003 never arrived. I want a refund.", "CUST002")
    approval = first["resolution"]["refund_approval"]
    review_refund_approval(approval["ApprovalID"], "approve", "Amit")

    repeated = run_workflow("I want a refund for ORD1003 again.", "CUST002")
    assert repeated["duplicate_request"] is True
    assert repeated["case_id"] == approval["CaseID"]
    assert "No duplicate case" in repeated["response"]
    assert len(query_table("refund_approvals")) == 1


def test_t5_guardrail_blocks_off_domain_query():
    result = run_workflow("Can you plan a 5-day trip to Manali for me?", "CUST001")
    assert result["domain_relevant"] is False
    assert result["case_created"] is False
    assert "outside DemoKart customer-support scope" in result["response"]
    assert len(query_table("cases")) == 0


def test_t4_damaged_product_creates_pending_evidence_case(monkeypatch, tmp_path):
    from src.services import damaged_workflow
    from src.tools.order_tools import get_order

    class FakeAssessment:
        def assess(self, image_path, expected_product, expected_category=""):
            assert expected_product == "Laptop"
            return {
                "product_match": "MATCH",
                "damaged": "YES",
                "confidence": 0.95,
                "reason": "Visible crack on the laptop body",
                "uploaded_product": "Laptop",
            }

    monkeypatch.setattr(damaged_workflow, "DamageAssessmentAgent", FakeAssessment)
    monkeypatch.setattr(damaged_workflow, "DATA_DIR", tmp_path)

    order = get_order("ORD1099")

    class Upload:
        name = "damaged_laptop.png"
        def getbuffer(self):
            return b"fake-image-bytes"

    result = damaged_workflow.process_damage_upload("CUST003", order, Upload())
    assert result["assessment"]["product_match"] == "MATCH"
    assert result["assessment"]["damaged"] == "YES"
    assert result["case"]["CustomerID"] == "CUST003"

    from src.services.damaged_product_service import list_pending_damage_requests
    pending = list_pending_damage_requests()
    assert len(pending) == 1
    assert pending[0]["OrderID"] == "ORD1099"
    assert Path(pending[0]["EvidencePath"]).exists()
