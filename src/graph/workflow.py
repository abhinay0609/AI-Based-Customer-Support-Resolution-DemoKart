from langgraph.graph import START,END,StateGraph
from src.graph.state import WorkflowState
from src.graph.nodes import *
from src.graph.edges import after_guardrail,after_check,after_router,after_validation

def build_workflow():
    g=StateGraph(WorkflowState)
    for name,fn in [("preprocess",preprocess),("understand_query",understand_query),("guardrail",guardrail_node),
                    ("retrieve_case_context",retrieve_case_context_node),("create_or_update_case",create_or_update_case),
                    ("check_information",check_information),("planner",planner_node),("router",router_node),
                    ("rag",rag_node),("order_lookup",order_lookup_node),("tracking_lookup",tracking_lookup_node),
                    ("resolution",resolution_node),("validation",validation_node),("human_escalation",human_escalation_node),
                    ("response_generation",response_generation_node),("case_closure",case_closure_node),("audit_logging",audit_logging_node)]:
        g.add_node(name,fn)
    g.add_edge(START,"preprocess"); g.add_edge("preprocess","understand_query"); g.add_edge("understand_query","guardrail")
    g.add_conditional_edges("guardrail",after_guardrail,{"response_generation":"response_generation","case_context":"retrieve_case_context"})
    g.add_edge("retrieve_case_context","create_or_update_case"); g.add_edge("create_or_update_case","check_information")
    g.add_conditional_edges("check_information",after_check,{"response_generation":"response_generation","planner":"planner"})
    g.add_edge("planner","router")
    g.add_conditional_edges("router",after_router,{"rag":"rag","order_lookup":"order_lookup","tracking_lookup":"tracking_lookup","resolution":"resolution"})
    g.add_edge("rag","resolution"); g.add_edge("order_lookup","resolution"); g.add_edge("tracking_lookup","resolution")
    g.add_edge("resolution","validation")
    g.add_conditional_edges("validation",after_validation,{"human_escalation":"human_escalation","response_generation":"response_generation"})
    g.add_edge("human_escalation","response_generation"); g.add_edge("response_generation","case_closure"); g.add_edge("case_closure","audit_logging"); g.add_edge("audit_logging",END)
    return g.compile()

def run_workflow(query,customer_id="",order_id="",case_id=""):
    return build_workflow().invoke({"query":query,"customer_id":customer_id,"order_id":order_id,"case_id":case_id})
