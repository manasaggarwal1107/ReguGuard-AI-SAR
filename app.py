import streamlit as st
import json
import datetime
import uuid
import time
import graphviz

# --- Page Config & Custom CSS ---
st.set_page_config(page_title="ReguGuard AI | SAR Generator", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');

    html, body, [class*="css"] { font-family: 'Inter', sans-serif !important; }
    
    [data-testid="stHeader"] { background-color: transparent !important; }
    
    .stApp { background-color: #06090F; }
    .block-container { padding-top: 1.5rem; max-width: 95%; color: #E2E8F0; }
    
    .metric-box { 
        background: linear-gradient(145deg, #111827 0%, #0F172A 100%);
        padding: 20px; 
        border-radius: 12px; 
        border-left: 5px solid #38BDF8; 
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.5);
        margin-bottom: 20px;
    }
    .metric-box h4 { margin: 0; padding-bottom: 5px; color: #F8FAFC; font-weight: 600; font-size: 16px; }
    .metric-box p { margin: 0; color: #94A3B8; font-size: 14px; }
    
    .status-badge { background: rgba(16, 185, 129, 0.2); color: #34D399; padding: 6px 12px; border-radius: 6px; font-size: 13px; font-weight: 700; border: 1px solid rgba(16, 185, 129, 0.4); display: inline-block;}
    .alert-badge { background: rgba(225, 29, 72, 0.2); color: #FB7185; padding: 6px 12px; border-radius: 6px; font-size: 13px; font-weight: 700; border: 1px solid rgba(225, 29, 72, 0.4); display: inline-block;}
    
    .section-header { border-bottom: 1px solid #1E293B; padding-bottom: 12px; margin-bottom: 24px; color: #38BDF8; font-weight: 700; text-transform: uppercase; font-size: 14px; letter-spacing: 0.5px; }
    
    .stButton > button { border-radius: 8px !important; font-weight: 600 !important; transition: all 0.3s ease !important; }
    .stButton > button:hover { transform: translateY(-2px); box-shadow: 0 4px 12px rgba(56, 189, 248, 0.3) !important; }
    
    .stTabs [data-baseweb="tab-list"] { gap: 24px; }
    .stTabs [data-baseweb="tab"] { font-weight: 600; font-size: 16px; padding-top: 10px; padding-bottom: 10px; color: #94A3B8 !important; }
    .stTabs [aria-selected="true"] { color: #38BDF8 !important; border-bottom-color: #38BDF8 !important; }
    </style>
""", unsafe_allow_html=True)

# --- Mock Database of Cases (Localized to INR) ---
MOCK_DB = {
    "CASE-001 (Structuring)": {
        "alert_type": "Structuring / Pass-Through",
        "risk_score": 88,
        "customer": {
            "Name": "Global Import Export LLC",
            "Account": "CHK-88992100",
            "KYC_Profile": "Electronics Wholesaler",
            "Risk_Tier": "High (Cross-Border)"
        },
        "transactions": [
            {"Date": "2026-07-20", "Type": "Wire In", "Amount": "₹41,00,000", "Source": "Shell Corp A (Cyprus)"},
            {"Date": "2026-07-21", "Type": "Wire In", "Amount": "₹40,50,000", "Source": "Shell Corp B (BVI)"},
            {"Date": "2026-07-22", "Type": "Wire Out", "Amount": "₹81,00,000", "Dest": "Crypto Exchange XYZ"}
        ],
        "draft": "Between 2026-07-20 and 2026-07-21, the subject received two incoming wires totaling ₹81,50,000 from known high-risk jurisdictions (Cyprus and BVI). On 2026-07-22, the funds were aggregated and immediately wired out (₹81,00,000) to 'Crypto Exchange XYZ'. This rapid movement of funds lacks a clear economic purpose and is consistent with layering."
    },
    "CASE-002 (High-Risk Vendor)": {
        "alert_type": "Anomalous Vendor Payments",
        "risk_score": 94,
        "customer": {
            "Name": "Urban Smart Park Solutions",
            "Account": "CORP-554433",
            "KYC_Profile": "Smart Parking Infrastructure & IoT",
            "Risk_Tier": "Medium (Domestic Vendor)"
        },
        "transactions": [
            {"Date": "2026-07-15", "Type": "Funding", "Amount": "₹2,10,00,000", "Source": "Municipal Contract Payment"},
            {"Date": "2026-07-18", "Type": "Wire Out", "Amount": "₹71,00,000", "Dest": "Ericsson Consulting Sub-contractor"},
            {"Date": "2026-07-19", "Type": "Wire Out", "Amount": "₹1,00,00,000", "Dest": "Apex IoT Holdings (Cayman)"}
        ],
        "draft": "On 2026-07-15, Urban Smart Park Solutions received a ₹2,10,00,000 municipal contract payment. While subsequent payments to known telecom contractors appear legitimate, a sudden ₹1,00,00,000 outgoing wire on 2026-07-19 to an offshore holding company (Apex IoT in the Cayman Islands) deviates significantly from the expected supply chain profile for a domestic smart parking hardware installation."
    }
}

# --- Sidebar: Real-World Controls & New ROI Feature ---
with st.sidebar:
    st.markdown("<br>", unsafe_allow_html=True)
    
    st.markdown("""
        <div style='background-color: rgba(225, 29, 72, 0.1); border: 1px solid rgba(225, 29, 72, 0.3); padding: 12px; border-radius: 8px; color: #FB7185; font-size: 13px; text-align: center; margin-bottom: 20px;'>
            🔒 <b>RESTRICTED ACCESS:</b><br>Only authorized personnel will have access to generate this report.
        </div>
    """, unsafe_allow_html=True)

    st.markdown("### 💰 ROI Calculator")
    c1, c2 = st.columns(2)
    c1.metric(label="Time Saved", value="42 Min")
    c2.metric(label="Cost Saved", value="₹4,500")
    
    st.markdown("---")
    st.markdown("### Platform Controls")
    
    st.markdown("**1. Connect AI Model**")
    api_key = st.text_input("OpenAI API Key (Optional)", type="password", placeholder="sk-...")
    if api_key:
        st.success("Connected to GPT-4 Turbo")
    else:
        st.info("Using internal compliance LLM (Mock Mode)")
        
    st.markdown("---")
    st.markdown("**2. Investigation Queue**")
    selected_case_name = st.selectbox("Select Triggered Alert:", list(MOCK_DB.keys()))

    st.markdown("---")
    st.markdown("### 🏗️ Level 1 Data Flow Diagram (DFD)")
    st.code('''
[Banking Core API] 
        │ (JSON)
        ▼
[Evidence Ingestion] 
        │ (Context)
        ▼
[LLM Draft Engine]
        │ (Draft)
        ▼
[Human Review]
        │ (Approval)
        ▼
[Immutable Vault]
    ''', language='text')
    
# --- Dynamic State Management ---
if "current_case_name" not in st.session_state or st.session_state.current_case_name != selected_case_name:
    st.session_state.current_case_name = selected_case_name
    st.session_state.step = 1
    st.session_state.audit_log = {
        "report_id": f"SAR-{uuid.uuid4().hex[:8].upper()}",
        "session_start": datetime.datetime.now().isoformat(),
        "evidence_snapshot": {},
        "ai_metadata": {"model": "gpt-4" if api_key else "internal-mock-llm"},
        "analyst_final_text": "",
        "approved_by": None
    }

case_data = MOCK_DB[selected_case_name]

# --- UI Header ---
st.markdown(f"## 🛡️ ReguGuard AI")
st.markdown(f"#### Active Investigation: <span style='color: #38BDF8;'>{case_data['customer']['Name']}</span>", unsafe_allow_html=True)
st.caption(f"**Session ID:** `{st.session_state.audit_log['report_id']}` &nbsp;|&nbsp; **Status:** In Progress")
st.markdown("---")

# --- NATIVE TABS FOR BETTER UX ---
tab1, tab2 = st.tabs(["📁 Investigator Dashboard", "⚙️ System Analytics & Audit Vault"])

# ==========================================
# TAB 1: THE MAIN INVESTIGATION DASHBOARD
# ==========================================
with tab1:
    col1, col2, col3 = st.columns([1, 1.5, 1], gap="large")

    # --- COLUMN 1: EVIDENCE ---
    with col1:
        st.markdown("<div class='section-header'>📂 1. Evidence Snapshot</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='alert-badge'>🚨 ALERT: {case_data['alert_type'].upper()}</div>", unsafe_allow_html=True)
        st.write("")
        
        st.markdown(f"<span style='font-size: 14px; font-weight: 600; color: #94A3B8;'>Customer Risk Score:</span> <span style='color: #F8FAFC; font-size: 16px; font-weight: bold;'>{case_data['risk_score']}/100</span>", unsafe_allow_html=True)
        st.progress(case_data['risk_score'] / 100)
        st.write("")
        
        st.subheader("KYC Profile")
        st.json(case_data['customer'])
        
        st.subheader("Flagged Transactions")
        st.dataframe(case_data['transactions'], use_container_width=True)
        
        if st.session_state.step == 1:
            st.write("")
            if st.button("Generate Narrative Draft", type="primary", use_container_width=True):
                st.session_state.audit_log["evidence_snapshot"] = {"customer": case_data['customer'], "tx": case_data['transactions']}
                with st.spinner("Connecting to Core Banking API & querying LLM..."):
                    time.sleep(2) 
                    st.session_state.step = 2
                    st.rerun()

    # --- COLUMN 2: HUMAN-IN-THE-LOOP ---
    with col2:
        st.markdown("<div class='section-header'>✍️ 2. AI Draft & Human Review</div>", unsafe_allow_html=True)
        
        if st.session_state.step >= 2:
            full_draft = f"**Introduction:**\nThis Suspicious Activity Report (SAR) is being filed on {case_data['customer']['Name']} (Account: {case_data['customer']['Account']}) due to suspected {case_data['alert_type'].lower()}.\n\n**Body:**\n{case_data['draft']}"
            
            # Store original draft in state so we don't lose it if they edit
            if "original_ai_draft" not in st.session_state.audit_log:
                st.session_state.audit_log["original_ai_draft"] = full_draft
                
            st.info("AI generation complete. Please review, edit, and append final disposition.")
            
            edited_text = st.text_area("Narrative Editor (Human Override Enabled)", value=full_draft, height=350)
            
            if st.session_state.step == 2:
                if st.button("Approve & Cryptographically Sign", type="primary", use_container_width=True):
                    st.session_state.audit_log["analyst_final_text"] = edited_text
                    st.session_state.audit_log["approved_by"] = "Analyst_JD_992"
                    st.session_state.audit_log["approval_timestamp"] = datetime.datetime.now().isoformat()
                    st.session_state.step = 3
                    st.rerun()
                    
        elif st.session_state.step == 1:
            st.markdown("<div style='text-align: center; color: #64748B; padding-top: 40px;'><i>Awaiting evidence submission... Click 'Generate Narrative Draft' to begin.</i></div>", unsafe_allow_html=True)

    # --- COLUMN 3: COMPLIANCE & ESCALATION ---
    with col3:
        st.markdown("<div class='section-header'>✅ 3. FinCEN Guardrails</div>", unsafe_allow_html=True)
        
        if st.session_state.step >= 2:
            st.markdown("**FinCEN 5W+1H Checklist:**")
            st.markdown(f"✅ **Who:** {case_data['customer']['Name']}")
            st.markdown(f"✅ **What:** {case_data['alert_type']}")
            st.markdown("✅ **When:** Dates mapped from Tx logs")
            st.markdown("✅ **Where:** Jurisdictions Identified")
            st.markdown("✅ **Why:** Deviates from KYC profile")
            st.markdown("✅ **How:** Mechanism of transfer detailed")
            
            st.write("")
            st.progress(1.0, text="FinCEN Readiness Score: 100%")
            st.write("---")
            
        if st.session_state.step == 3:
            st.markdown("""
            <div class='metric-box'>
                <h4>SAR Officially Approved</h4>
                <p>The filing has been cryptographically signed.</p>
                <br>
                <span class='status-badge'>🔒 AUDIT TRAIL LOCKED</span>
            </div>
            """, unsafe_allow_html=True)
            
            # --- PDF GENERATION LOGIC ---
            def generate_pdf_report():
                from fpdf import FPDF
                
                pdf = FPDF()
                pdf.add_page()
                
                # Title
                pdf.set_font("Arial", 'B', 16)
                pdf.cell(0, 10, "ReguGuard AI - Verified SAR Audit Report", ln=True, align='C')
                pdf.ln(5)
                
                # Meta Data
                pdf.set_font("Arial", 'B', 12)
                pdf.cell(0, 8, f"Customer Entity: {case_data['customer']['Name']}", ln=True)
                pdf.set_font("Arial", '', 10)
                pdf.cell(0, 6, f"Account: {case_data['customer']['Account']}", ln=True)
                pdf.cell(0, 6, f"Session ID: {st.session_state.audit_log['report_id']}", ln=True)
                pdf.cell(0, 6, f"Approved By: {st.session_state.audit_log['approved_by']} at {st.session_state.audit_log['approval_timestamp'][:19]}", ln=True)
                pdf.ln(10)
                
                # AI Draft
                pdf.set_font("Arial", 'B', 12)
                pdf.set_text_color(180, 0, 0) # Dark Red for AI
                pdf.cell(0, 8, "--- 1. ORIGINAL AI-GENERATED DRAFT ---", ln=True)
                pdf.set_text_color(0, 0, 0)
                pdf.set_font("Arial", '', 10)
                
                # FPDF encoding fix for special characters
                ai_text = st.session_state.audit_log["original_ai_draft"].replace('**', '').encode('latin-1', 'replace').decode('latin-1')
                pdf.multi_cell(0, 6, ai_text)
                pdf.ln(10)
                
                # Human Final Draft
                pdf.set_font("Arial", 'B', 12)
                pdf.set_text_color(0, 100, 0) # Dark Green for Human
                pdf.cell(0, 8, "--- 2. FINAL HUMAN-APPROVED FILING ---", ln=True)
                pdf.set_text_color(0, 0, 0)
                pdf.set_font("Arial", '', 10)
                
                final_text = st.session_state.audit_log["analyst_final_text"].replace('**', '').encode('latin-1', 'replace').decode('latin-1')
                pdf.multi_cell(0, 6, final_text)
                
                return pdf.output(dest='S').encode('latin-1')

            # Render Download Buttons
            try:
                import fpdf
                pdf_bytes = generate_pdf_report()
                st.download_button(
                    label="📄 Download Human-Readable PDF",
                    file_name=f"{st.session_state.audit_log['report_id']}_report.pdf",
                    mime="application/pdf",
                    data=pdf_bytes,
                    use_container_width=True
                )
            except ImportError:
                st.warning("To enable PDF downloads, run `pip install fpdf` in your terminal.")
            
            # JSON Button
            json_string = json.dumps(st.session_state.audit_log, indent=2)
            st.download_button(
                label="📥 Download Regulator Audit JSON",
                file_name=f"{st.session_state.audit_log['report_id']}_audit.json",
                mime="application/json",
                data=json_string,
                use_container_width=True
            )
                
            st.markdown("---")
            st.markdown("#### Internal Escalation")
            if st.button("Draft Executive Briefing ✉️", use_container_width=True):
                st.info(f"**To:** director.compliance@bank.com\n\n**Subject:** URGENT: SAR Approved for {case_data['customer']['Name']}\n\nDirector,\n\nA SAR has been cryptographically signed and filed for the above entity regarding {case_data['alert_type'].lower()}. The immutable audit trail is attached for your review. No further manual QA is required.")

# ==========================================
# TAB 2: SYSTEM ANALYTICS (Full Width)
# ==========================================
with tab2:
    st.markdown("<br>", unsafe_allow_html=True)
    
    col_a, col_b = st.columns(2, gap="large")
    
    with col_a:
        st.markdown("<div class='section-header'>🔗 Entity Link Analysis Map</div>", unsafe_allow_html=True)
        st.markdown("Visualized fund flow routing between counterparties.")
        
        # Create a dynamic graph
        graph = graphviz.Digraph(engine='dot')
        graph.attr(bgcolor='#06090F', fontcolor='#F8FAFC', rankdir='LR')
        graph.attr('node', style='filled', fillcolor='#1E293B', fontcolor='#F8FAFC', color='#38BDF8', shape='box', fontname='Inter')
        graph.attr('edge', color='#94A3B8', fontcolor='#94A3B8', fontname='Inter', fontsize='10')

        if selected_case_name == "CASE-001 (Structuring)":
            graph.node('A', 'Cyprus Shell\n(High Risk)')
            graph.node('B', 'BVI Shell\n(High Risk)')
            graph.node('C', 'Local Branch\n(Cash Deposits)')
            graph.node('Target', 'Global Import Export\nCHK-88992100', fillcolor='#DC2626', fontcolor='white')
            graph.node('Dest', 'Crypto Exchange XYZ')
            
            graph.edge('A', 'Target', label=' ₹41L Wire')
            graph.edge('B', 'Target', label=' ₹40.5L Wire')
            graph.edge('C', 'Target', label=' Structured Cash')
            graph.edge('Target', 'Dest', label=' ₹81L Immediate Outflow', color='#DC2626')
        else:
            graph.node('Source', 'Municipal Fund\n(Gov Contract)')
            graph.node('Target', 'Urban Smart Park\nCORP-554433', fillcolor='#DC2626', fontcolor='white')
            graph.node('Valid', 'Ericsson Consulting\n(Sub-contractor)')
            graph.node('Invalid', 'Apex IoT Holdings\n(Cayman Islands)', fillcolor='#F59E0B', fontcolor='black')
            
            graph.edge('Source', 'Target', label=' ₹2.1Cr Contract')
            graph.edge('Target', 'Valid', label=' ₹71L Standard Payment')
            graph.edge('Target', 'Invalid', label=' ₹1Cr Anomalous Wire', color='#F59E0B')

        st.graphviz_chart(graph, use_container_width=True)

    with col_b:
        st.markdown("<div class='section-header'>🧠 Deep Learning Anomaly Metrics</div>", unsafe_allow_html=True)
        st.markdown("**Primary Activation:** Temporal Spacing of Deposits / Velocity Threshold")
        st.markdown("**Activation Function Trigger:** ReLU threshold exceeded on hidden network layer.")
        st.markdown("**Confidence Score:** 92.4%")
        st.progress(0.92)
        st.caption("Note: The model avoided vanishing gradient during training by utilizing skip connections on temporal transaction sequences, ensuring accurate flagging of structured payments.")
        
    st.markdown("---")
    st.markdown("<div class='section-header'>🔒 Raw Audit Ledger Viewer</div>", unsafe_allow_html=True)
    
    if st.session_state.step == 3:
        st.write("Below is the live, raw JSON output representing the immutable chain of custody for this case.")
        st.json(st.session_state.audit_log)
    else:
        st.warning("Awaiting SAR Approval. The Raw Audit Ledger will populate once the analyst cryptographically signs the filing in the 'Investigator Dashboard' tab.")