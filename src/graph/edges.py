def after_guardrail(s): return "response_generation" if s.get("current_action")=="guardrail" else "case_context"
def after_check(s): return "response_generation" if s.get("missing_information") else "planner"
def after_router(s): return s.get("current_action","resolution")
def after_validation(s): return "human_escalation" if s.get("escalation_required") else "response_generation"
