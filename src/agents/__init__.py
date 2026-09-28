"""Focused AI components used by the DemoKart LangGraph workflow.

AI roles:
- UnderstandingAgent: Gemini-based intent, domain guardrail and complexity understanding.
- OrderManagementAgent: authenticated order/tracking tool wrapper.
- DamageAssessmentAgent: Gemini Vision product-match and damage assessment.

Customer response generation also uses Gemini, while high-risk business state
changes remain deterministic and human-controlled.
"""
