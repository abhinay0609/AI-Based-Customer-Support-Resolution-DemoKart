# DemoKart Hybrid Agentic Customer Resolution

A focused enterprise-style MVP built with **LangGraph + Gemini + RAG + deterministic business controls**.

## Architecture

The solution deliberately uses a small number of AI components rather than many independent agents:

1. **Understanding Agent (Gemini)** – classifies intent, detects out-of-domain requests, extracts IDs and estimates confidence/complexity.
2. **Order Management Agent** – authenticated order/tracking operations; deterministic ownership checks protect customer data.
3. **Gemini Vision** – used only for damaged-product evidence: product match first, damage assessment second.

A LangGraph workflow orchestrates these with deterministic services for case state, duplicate prevention, refund rules, cancellation rules, validation, notifications and audit logging. **Gemini also generates the final customer response** when an API key is configured; safe fallbacks are used when it is unavailable.

### Main flow

```text
Customer Query
   ↓
LLM Understanding + Guardrail
   ↓
Case Context Retrieval
   ↓
Information Check
   ↓
Planner / Router
   ├── Policy RAG → LLM Response
   ├── Order/Tracking Agent → Resolution
   └── Refund/Complaint → Deterministic Rules + Human Review when required
   ↓
Validation
   ↓
LLM Response Generation
   ↓
Case State + Audit
```

### Damaged product → refund flow

```text
Customer selects owned order + uploads image
        ↓
Gemini Vision
        ↓
Product Match?
  ├─ Mismatch → Stage 1 human evidence review
  └─ Match → Damage check
                ├─ Damage YES → Stage 1 human evidence review
                ├─ Damage NO → Case closed, no return/refund
                └─ Uncertain → Stage 1 human evidence review

Stage 1 — Amit verifies evidence
        ↓
  Reject → Case closed; NO refund request
        │
  Approve/Modify
        ↓
Stage 2 — Refund request created
        ↓
Amit approves / modifies / rejects refund
        ↓
Case closed + customer notification
```

## Human-in-the-loop behavior

The Support Specialist queue starts **empty on a fresh installation**. No refund or damaged-product request is pre-seeded.

A request appears only after a customer actually submits:

- a refund request, or
- a damaged-product evidence request that needs human review.

Specialist: **Amit**

```text
Username: amit.support
Password: Amit@123
```

For a normal refund, Amit directly **Approves / Rejects / Modifies** the refund.

For a damaged product, Amit first reviews the **image evidence and AI product/damage assessment**. Only an Approve/Modify decision creates the separate Stage-2 refund request. The case stays open until the refund decision is completed. A Stage-1 Reject closes the case without creating a refund.

## Duplicate protection

Refund/damage requests are matched using authenticated **CustomerID + OrderID**. A second request for the same order does not create another case after a request is already pending or closed. To create a genuinely new issue, the customer must explicitly ask to create a new case.

## Customer credentials

All demo customers use:

```text
Password: Demo@123
```

Useful test accounts:

| Customer | Login |
|---|---|
| Rahul Sharma | `CUST001` |
| Priya Sharma | `CUST002` |
| Amit Mehta | `CUST003` |

The test data intentionally includes:

- `CUST001` → `ORD1002` for order lookup
- `CUST002` → `ORD1003` for refund testing
- `CUST003` → `ORD1099` (Laptop) for damaged-product testing

## Required setup

1. Create/activate a Python 3.12 virtual environment.
2. Install packages:

```powershell
python -m pip install -r requirements.txt
```

If PyPI SSL errors occur:

```powershell
python -m pip install -r requirements.txt --trusted-host pypi.org --trusted-host files.pythonhosted.org
```

3. Copy `.env.example` to `.env`.
4. Add your Gemini API key:

```text
GOOGLE_API_KEY=your_key_here
```

5. Start the application:

```powershell
python -m streamlit run app/streamlit_app.py
```

The first startup creates `data/operational.db` from the clean CSV data. Do not copy an old operational database into a fresh demo if you want the specialist queue to remain empty.

## Five acceptance tests

| # | Scenario | Login | Query / Action | Expected |
|---|---|---|---|---|
| T1 | General Enquiry | `CUST001` | `What is your refund policy?` | RAG + contextual response |
| T2 | Order Lookup | `CUST001` | `What is the current status of my order ORD1002?` | Authenticated order/tracking result |
| T3 | Refund | `CUST002` | `My order ORD1003 never arrived. I want a refund.` | Case + pending refund for Amit |
| T4 | Damaged Product | `CUST003` | `My laptop ORD1099 arrived damaged. I want a refund.` + upload damaged laptop image | Gemini product match + damage assessment + human review |
| T5 | Guardrail | `CUST001` | `Can you plan a 5-day trip to Manali for me?` | Out-of-scope response; no case |

For T4, use a clear photo of a laptop with visible damage. The application first checks that the image appears to be the ordered product before assessing damage.

## Fresh-start reset

If you have already run the application and want a completely clean demo queue, stop Streamlit and delete:

```text
data/operational.db
vectorstore/
```

Then restart the application. The CSV files are the source of truth and contain **no pre-seeded support cases**.
