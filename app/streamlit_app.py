import sys
from pathlib import Path
import streamlit as st

PROJECT_ROOT=Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path: sys.path.insert(0,str(PROJECT_ROOT))

from src.services.auth_service import authenticate_customer, authenticate_specialist, SPECIALIST_NAME
from src.services.seed_data import seed_demo_cases
from src.tools.customer_tools import get_customer_orders
from src.tools.case_tools import get_customer_cases
from src.services.notification_service import get_notifications,mark_read
from src.graph.workflow import run_workflow
from src.services.damaged_workflow import process_damage_upload
from src.tools.order_tools import get_order
from src.rag.vectorstore import initialize_rag

st.set_page_config(page_title="DemoKart AI Customer Resolution",page_icon="🛍️",layout="wide")
seed_demo_cases()

def logout():
    for k in list(st.session_state.keys()): del st.session_state[k]
    st.rerun()

def login_screen():
    st.title("🛍️ DemoKart AI Customer Resolution")
    st.caption("Enterprise-style hybrid Agentic AI customer support")
    role=st.radio("Login as",["Customer","Support Specialist"],horizontal=True)
    with st.form("login"):
        if role=="Customer":
            user=st.text_input("Customer ID",placeholder="CUST001")
            pwd=st.text_input("Password",type="password",value="")
        else:
            user=st.text_input("Specialist username",placeholder="amit.support")
            pwd=st.text_input("Password",type="password")
        ok=st.form_submit_button("Login",type="primary")
    if ok:
        if role=="Customer":
            customer=authenticate_customer(user,pwd)
            if customer:
                st.session_state.update(authenticated=True,role="customer",customer=customer)
                st.rerun()
            else: st.error("Invalid customer ID or password.")
        else:
            if authenticate_specialist(user,pwd):
                st.session_state.update(authenticated=True,role="specialist",specialist=SPECIALIST_NAME)
                st.rerun()
            else: st.error("Invalid specialist credentials.")
    with st.expander("Demo credentials"):
        st.code("Customer: CUST001 / Demo@123\nSupport Specialist: amit.support / Amit@123")

def customer_portal():
    customer=st.session_state["customer"]; cid=customer["CustomerID"]
    st.sidebar.title(f"Welcome, {customer['CustomerName']}")
    st.sidebar.caption(cid)
    if st.sidebar.button("Logout"): logout()
    page=st.sidebar.radio("Portal",["Dashboard","AI Support","Damaged Product","Case History","Notifications"])
    orders=get_customer_orders(cid)
    if page=="Dashboard":
        st.title("Customer Dashboard")
        st.write("Your orders and support activity")
        if orders:
            st.dataframe(orders,use_container_width=True,hide_index=True)
        else: st.info("No orders found.")
        unread=get_notifications(cid,True)
        if unread: st.warning(f"You have {len(unread)} unread notification(s).")
    elif page=="AI Support":
        st.title("AI Support")
        st.caption("LLM understanding + LangGraph orchestration + deterministic business rules + RAG")
        order_ids=[""]+[x["OrderID"] for x in orders]
        selected_order=st.selectbox("Optional order context",order_ids)
        case_ids=[""]+[x["CaseID"] for x in get_customer_cases(cid)]
        selected_case=st.selectbox("Optional case context",case_ids)
        for item in st.session_state.get("chat_history",[]):
            with st.chat_message("user"): st.write(item["q"])
            with st.chat_message("assistant"): st.write(item["a"])
        q=st.chat_input("Ask about orders, refunds, cancellation, returns, complaints, policies or cases")
        if q:
            with st.spinner("Understanding and resolving your request..."):
                state=run_workflow(q,cid,selected_order,selected_case)
            st.session_state.setdefault("chat_history",[]).append({"q":q,"a":state.get("response","")})
            st.session_state["last_state"]=state
            st.rerun()
        state=st.session_state.get("last_state")
        if state:
            st.divider()
            st.subheader("Latest resolution")
            st.write(state.get("response",""))
            if state.get("retrieved_documents"):
                with st.expander("📚 RAG evidence used"):
                    st.code(state.get("retrieved_documents",""), language="text")
            c1,c2,c3,c4=st.columns(4)
            c1.metric("Intent",state.get("intent",""))
            c2.metric("AI confidence",f"{state.get('understanding_confidence',0):.0%}")
            c3.metric("Case",state.get("case_id") or "None")
            c4.metric("Status",state.get("case_status") or state.get("resolution",{}).get("status",""))
            if state.get("duplicate_request"):
                st.info("Duplicate protection: the same order already has a refund/damage request. No new case was created.")
    elif page=="Damaged Product":
        st.title("Damaged Product — AI Evidence Check")
        st.write("Upload evidence. Gemini first checks product identity, then checks damage only when the product matches.")
        eligible_orders=[o for o in orders if o.get("Status","").casefold() not in {"cancelled"}]
        if not eligible_orders: st.info("No eligible orders available.")
        else:
            labels={f"{o['OrderID']} — {o['Product']} ({o['Status']})":o for o in eligible_orders}
            label=st.selectbox("Select the order",list(labels))
            order=labels[label]
            uploaded=st.file_uploader("Upload product image",type=["png","jpg","jpeg","webp"])
            if uploaded and st.button("Analyze evidence",type="primary"):
                with st.spinner("Gemini is checking product match and visible damage..."):
                    result=process_damage_upload(cid,order,uploaded)
                if result.get("duplicate"):
                    st.warning(result["message"])
                else:
                    a=result["assessment"]
                    st.subheader("AI evidence result")
                    st.write(f"**Product match:** {a['product_match']}")
                    st.write(f"**Damage detected:** {a['damaged']}")
                    st.write(f"**Confidence:** {a['confidence']:.0%}")
                    st.write(f"**Evidence:** {a['reason']}")
                    if a["product_match"]=="MATCH" and a["damaged"]=="YES":
                        st.success(f"Damage verification request created and escalated to Support Specialist Amit. Case {result['case']['CaseID']}. No refund approval has been created yet.")
                    elif a["product_match"]=="MISMATCH":
                        st.warning(f"Product mismatch flagged and escalated to Amit. Case {result['case']['CaseID']}.")
                    else:
                        st.info(f"{result['summary']} Case {result['case']['CaseID']}.")
    elif page=="Case History":
        st.title("Case History")
        cases=get_customer_cases(cid)
        if cases: st.dataframe(cases,use_container_width=True,hide_index=True)
        else: st.info("No cases.")
    elif page=="Notifications":
        st.title("Notifications")
        notes=get_notifications(cid)
        if not notes: st.info("No notifications.")
        for n in notes:
            with st.container(border=True):
                st.write(n["Message"])
                st.caption(f"Case: {n.get('CaseID') or '—'} | Order: {n.get('OrderID') or '—'} | {n['CreatedAt']}")
                if not n["IsRead"] and st.button("Mark as read",key=f"read_{n['NotificationID']}"):
                    mark_read(n["NotificationID"],cid); st.rerun()

def specialist_portal():
    st.sidebar.title("Support Specialist")
    st.sidebar.write("Logged in as **Amit**")
    if st.sidebar.button("Logout"): logout()
    st.title("🧑‍💼 Support Specialist Console")
    st.caption("Human-in-the-loop governance: AI provides evidence/context; Amit makes the final decision.")
    from src.services.refund_approval_service import list_pending_refund_approvals,review_refund_approval
    from src.services.damaged_product_service import list_pending_damage_requests,review_damage_request
    refunds=list_pending_refund_approvals(); damages=list_pending_damage_requests()
    st.metric("Pending refunds",len(refunds)); st.metric("Pending damaged-product cases",len(damages))
    tabs=st.tabs(["Refund Requests","Damaged Product Verification"])
    with tabs[0]:
        if not refunds: st.success("No pending refund requests.")
        for r in refunds:
            with st.container(border=True):
                st.subheader(f"Case {r['CaseID']} — Order {r['OrderID']}")
                st.write(f"Customer: **{r['CustomerID']}** | Requested amount: **₹{float(r['RequestedAmount']):g}**")
                st.write(f"Reason: {r['Reason']}")
                decision=st.selectbox("Decision",["Approve","Modify","Reject"],key=f"rd_{r['ApprovalID']}")
                amount=st.number_input("Approved amount",min_value=0.0,max_value=float(r["RequestedAmount"]),value=float(r["RequestedAmount"]),step=100.0,key=f"amt_{r['ApprovalID']}",disabled=decision!="Modify")
                note=st.text_area("Specialist note",key=f"rn_{r['ApprovalID']}")
                if st.button("Submit decision",key=f"submit_{r['ApprovalID']}",type="primary"):
                    action={"Approve":"approve","Modify":"modify","Reject":"reject"}[decision]
                    try:
                        reviewed=review_refund_approval(r["ApprovalID"],action,"Amit",amount if action=="modify" else None,note)
                        st.success(f"{reviewed['OrderID']} reviewed. Case {reviewed['CaseID']} is now closed.")
                        st.rerun()
                    except ValueError as e: st.error(str(e))
    with tabs[1]:
        if not damages: st.success("No pending damaged-product requests.")
        for d in damages:
            with st.container(border=True):
                st.subheader(f"Case {d['CaseID']} — Order {d['OrderID']}")
                st.write(f"Customer: **{d['CustomerID']}**")
                st.write(f"Ordered product: **{d['ExpectedProduct']}**")
                st.write(f"AI product match: **{d['ProductMatch']}** | AI damage: **{d['DamageDetected']}** | Confidence: **{float(d['AIConfidence']):.0%}**")
                st.info("Stage 1: Amit verifies the evidence. Approve/Modify creates the Stage 2 refund request; Reject closes the case without creating a refund.")
                st.write(f"AI evidence note: {d['AIReason']}")
                evidence=Path(d["EvidencePath"])
                if evidence.exists(): st.image(str(evidence),caption=f"Customer evidence: {d['EvidenceName']}",use_container_width=True)
                else: st.error("Evidence file is missing.")
                decision=st.selectbox("Decision",["Approve","Modify","Reject"],key=f"dd_{d['RequestID']}")
                note=st.text_area("Specialist note",key=f"dn_{d['RequestID']}")
                if st.button("Submit damage decision",key=f"ds_{d['RequestID']}",type="primary"):
                    try:
                        reviewed=review_damage_request(d["RequestID"],decision,"Amit",note)
                        if decision in {"Approve", "Modify"}:
                            st.success(f"Damage verification approved for {reviewed['OrderID']}. A separate refund request is now pending in the Refund Requests tab.")
                        else:
                            st.success(f"Damage verification rejected for {reviewed['OrderID']}. Case {reviewed['CaseID']} is closed and no refund was created.")
                        st.rerun()
                    except ValueError as e: st.error(str(e))

if not st.session_state.get("authenticated"):
    login_screen()
elif st.session_state.get("role")=="customer":
    customer_portal()
else:
    specialist_portal()
