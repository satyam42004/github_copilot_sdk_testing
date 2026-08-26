import json
import os
import sqlite3
import time
from pathlib import Path
from dotenv import load_dotenv
import streamlit as st

load_dotenv()

# LangSmith / LangChain Observability configuration
os.environ["LANGCHAIN_TRACING_V2"] = os.getenv("LANGSMITH_TRACING", "false")
os.environ["LANGCHAIN_API_KEY"] = os.getenv("LANGSMITH_API_KEY", "")
os.environ["LANGCHAIN_PROJECT"] = os.getenv("LANGSMITH_PROJECT", "enterprise-knowledge-assistant")
os.environ["LANGCHAIN_ENDPOINT"] = os.getenv("LANGSMITH_ENDPOINT", "https://api.smith.langchain.com")

from graph.workflow import build_graph
from rag.vector_store import VectorStore
from rag.document_loader import load_documents

# --------------------------------------------------
# Page Configuration
# --------------------------------------------------
st.set_page_config(
    page_title="Enterprise Knowledge Assistant | LangGraph + RAG + RAGAS + MCP",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --------------------------------------------------
# Master CSS Design System (Ultra-Modern Executive Theme)
# --------------------------------------------------
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&family=Inter:wght@300;400;500;600;700&display=swap');

    /* Global Typography */
    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    h1, h2, h3, h4, .main-title {
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        letter-spacing: -0.025em;
    }

    code, pre {
        font-family: 'JetBrains Mono', monospace !important;
    }

    /* Executive Hero Header */
    .hero-container {
        position: relative;
        background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 40%, #31104b 100%);
        border: 1px solid rgba(255, 255, 255, 0.12);
        border-radius: 20px;
        padding: 28px 32px;
        margin-bottom: 24px;
        box-shadow: 0 20px 40px -15px rgba(15, 23, 42, 0.7), inset 0 1px 1px rgba(255, 255, 255, 0.15);
        overflow: hidden;
    }

    .hero-container::before {
        content: '';
        position: absolute;
        top: -50%;
        right: -20%;
        width: 300px;
        height: 300px;
        background: radial-gradient(circle, rgba(168, 85, 247, 0.25) 0%, rgba(99, 102, 241, 0) 70%);
        border-radius: 50%;
        pointer-events: none;
    }

    .hero-title-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        flex-wrap: wrap;
        gap: 12px;
        margin-bottom: 8px;
    }

    .hero-title {
        font-size: 2.1rem;
        font-weight: 800;
        background: linear-gradient(135deg, #ffffff 0%, #cbd5e1 60%, #a5b4fc 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        letter-spacing: -0.03em;
        margin: 0;
    }

    .live-status-pill {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        padding: 6px 14px;
        background: rgba(16, 185, 129, 0.12);
        border: 1px solid rgba(16, 185, 129, 0.3);
        border-radius: 9999px;
        color: #34d399;
        font-size: 0.8rem;
        font-weight: 600;
        letter-spacing: 0.03em;
    }

    .status-dot {
        width: 8px;
        height: 8px;
        background-color: #10b981;
        border-radius: 50%;
        box-shadow: 0 0 8px #10b981;
        animation: pulse-green 2s infinite;
    }

    @keyframes pulse-green {
        0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7); }
        70% { transform: scale(1); box-shadow: 0 0 0 6px rgba(16, 185, 129, 0); }
        100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(16, 185, 129, 0); }
    }

    .hero-subtitle {
        color: #94a3b8;
        font-size: 0.96rem;
        margin-bottom: 16px;
        line-height: 1.5;
        max-width: 900px;
    }

    /* Badges & Tags */
    .badge-bar {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
    }

    .tech-badge {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 4px 12px;
        border-radius: 8px;
        font-size: 0.76rem;
        font-weight: 600;
        background: rgba(255, 255, 255, 0.06);
        color: #e2e8f0;
        border: 1px solid rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(8px);
    }

    /* Glassmorphism Dashboard Cards */
    .glass-card {
        background: linear-gradient(135deg, rgba(30, 41, 59, 0.6) 0%, rgba(15, 23, 42, 0.6) 100%);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 14px;
        padding: 18px 22px;
        margin-bottom: 16px;
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.2);
    }

    /* RAGAS Metric Card */
    .ragas-container {
        background: linear-gradient(135deg, rgba(15, 23, 42, 0.85) 0%, rgba(30, 27, 75, 0.85) 100%);
        border: 1px solid rgba(139, 92, 246, 0.25);
        border-radius: 14px;
        padding: 18px 22px;
        margin: 14px 0;
        box-shadow: 0 8px 20px -4px rgba(139, 92, 246, 0.15);
    }

    .ragas-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 14px;
        border-bottom: 1px solid rgba(255, 255, 255, 0.08);
        padding-bottom: 8px;
    }

    .ragas-title {
        font-size: 0.9rem;
        font-weight: 700;
        color: #c4b5fd;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    .quality-chip-good {
        padding: 3px 12px;
        border-radius: 9999px;
        font-size: 0.78rem;
        font-weight: 700;
        background: rgba(16, 185, 129, 0.18);
        color: #34d399;
        border: 1px solid rgba(16, 185, 129, 0.4);
    }

    .quality-chip-moderate {
        padding: 3px 12px;
        border-radius: 9999px;
        font-size: 0.78rem;
        font-weight: 700;
        background: rgba(245, 158, 11, 0.18);
        color: #fbbf24;
        border: 1px solid rgba(245, 158, 11, 0.4);
    }

    .quality-chip-low {
        padding: 3px 12px;
        border-radius: 9999px;
        font-size: 0.78rem;
        font-weight: 700;
        background: rgba(239, 68, 68, 0.18);
        color: #f87171;
        border: 1px solid rgba(239, 68, 68, 0.4);
    }

    /* Ticket Card */
    .ticket-card {
        background: linear-gradient(135deg, rgba(15, 23, 42, 0.9) 0%, rgba(30, 41, 59, 0.9) 100%);
        border: 1px solid #334155;
        border-left: 5px solid #6366f1;
        border-radius: 14px;
        padding: 20px 24px;
        margin: 14px 0;
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.3);
    }

    .ticket-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 12px;
    }

    .ticket-id {
        font-family: 'JetBrains Mono', monospace;
        font-size: 1.05rem;
        font-weight: 700;
        color: #818cf8;
        background: rgba(99, 102, 241, 0.18);
        padding: 3px 10px;
        border-radius: 6px;
        border: 1px solid rgba(99, 102, 241, 0.3);
    }

    .priority-badge-high, .priority-badge-critical {
        background: rgba(239, 68, 68, 0.2);
        color: #f87171;
        border: 1px solid rgba(239, 68, 68, 0.4);
        padding: 4px 12px;
        border-radius: 9999px;
        font-size: 0.76rem;
        font-weight: 700;
        text-transform: uppercase;
    }

    .priority-badge-medium {
        background: rgba(245, 158, 11, 0.2);
        color: #fbbf24;
        border: 1px solid rgba(245, 158, 11, 0.4);
        padding: 4px 12px;
        border-radius: 9999px;
        font-size: 0.76rem;
        font-weight: 700;
        text-transform: uppercase;
    }

    .priority-badge-low {
        background: rgba(59, 130, 246, 0.2);
        color: #60a5fa;
        border: 1px solid rgba(59, 130, 246, 0.4);
        padding: 4px 12px;
        border-radius: 9999px;
        font-size: 0.76rem;
        font-weight: 700;
        text-transform: uppercase;
    }

    .status-badge-open {
        background: rgba(16, 185, 129, 0.2);
        color: #34d399;
        border: 1px solid rgba(16, 185, 129, 0.4);
        padding: 4px 12px;
        border-radius: 9999px;
        font-size: 0.76rem;
        font-weight: 700;
        text-transform: uppercase;
    }

    /* Trace Stepper */
    .trace-stepper {
        display: flex;
        flex-wrap: wrap;
        align-items: center;
        gap: 6px;
        padding: 10px 14px;
        background: rgba(15, 23, 42, 0.6);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 10px;
        margin: 8px 0;
    }

    .trace-node {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 4px 10px;
        border-radius: 6px;
        font-size: 0.78rem;
        font-family: 'JetBrains Mono', monospace;
        font-weight: 600;
        background: rgba(99, 102, 241, 0.15);
        color: #a5b4fc;
        border: 1px solid rgba(99, 102, 241, 0.3);
    }

    .trace-arrow {
        color: #64748b;
        font-size: 0.75rem;
    }

    /* Sidebar quick action button styling */
    div.stButton > button {
        border-radius: 8px;
        transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
        text-align: left;
        font-weight: 500;
    }
    div.stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    }

    /* Tabs styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
        border-bottom: 1px solid rgba(255, 255, 255, 0.08);
        margin-bottom: 16px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 44px;
        border-radius: 8px 8px 0 0;
        font-weight: 600;
        font-size: 0.9rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# --------------------------------------------------
# Resources & Graph Initialization
# --------------------------------------------------
def get_graph():
    return build_graph()


@st.cache_resource
def get_vector_store_count():
    try:
        vs = VectorStore()
        return vs.count()
    except Exception:
        return 0


def get_sqlite_tickets():
    db_path = Path(__file__).resolve().parent / "data" / "tickets.db"
    if not db_path.exists():
        return []
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        rows = conn.execute("SELECT id, title, description, priority, status FROM tickets ORDER BY id DESC").fetchall()
        conn.close()
        return [dict(r) for r in rows]
    except Exception:
        return []


graph = get_graph()
doc_count = get_vector_store_count()

# --------------------------------------------------
# Session State
# --------------------------------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []

if "preset_prompt" not in st.session_state:
    st.session_state.preset_prompt = None

if "last_state" not in st.session_state:
    st.session_state.last_state = None


# --------------------------------------------------
# Sidebar Configuration
# --------------------------------------------------
with st.sidebar:
    st.markdown("### 🏢 Executive Dashboard")
    st.caption("Agentic AI Enterprise Knowledge Platform")

    # Live Telemetry Box
    st.markdown(
        f"""
        <div style="background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.08); border-radius: 12px; padding: 14px; margin-bottom: 16px;">
            <div style="font-size: 0.75rem; color: #94a3b8; font-weight: 700; letter-spacing: 0.05em; margin-bottom: 8px;">SYSTEM TELEMETRY</div>
            <div style="display: flex; flex-direction: column; gap: 7px; font-size: 0.83rem;">
                <div style="display:flex; justify-content:space-between;"><span>🧠 <b>LangGraph:</b></span> <span style="color:#34d399;">Active (7 Nodes)</span></div>
                <div style="display:flex; justify-content:space-between;"><span>📚 <b>Knowledge Vectors:</b></span> <span style="color:#38bdf8; font-weight:600;">{doc_count} Chunks</span></div>
                <div style="display:flex; justify-content:space-between;"><span>📊 <b>RAGAS Metrics:</b></span> <span style="color:#c084fc;">Faithful + Relevancy</span></div>
                <div style="display:flex; justify-content:space-between;"><span>🔌 <b>MCP Server:</b></span> <span style="color:#fbbf24;">FastMCP SQLite</span></div>
                <div style="display:flex; justify-content:space-between;"><span>🛡️ <b>Guardrails:</b></span> <span style="color:#f87171;">Presidio PII Active</span></div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("### ⚡ Interactive Prompts")
    st.caption("Select a scenario to execute end-to-end:")

    sample_prompts = [
        ("🏖️ Leave Policy (Permanent Staff)", "How many days of leave does a permanent employee get?"),
        ("💻 IT Support & VPN Troubleshooting", "What is the procedure for IT support and VPN troubleshooting?"),
        ("✈️ Business Travel & Daily Allowance", "What is the daily meal allowance and hotel policy for domestic business travel?"),
        ("🔒 Cybersecurity & Password Rules", "What are the company password requirements and authentication rules?"),
        ("🏠 Hybrid & Remote Work Policy", "What does the company policy say about working from home?"),
        ("🎫 Raise High Priority Ticket (MCP)", "Create a high priority support ticket because employees cannot connect to the corporate VPN."),
        ("🛡️ Test PII Security Guardrail", "My email is employee@example.com. What is the leave policy?"),
    ]

    for label, prompt_text in sample_prompts:
        if st.button(label, use_container_width=True):
            st.session_state.preset_prompt = prompt_text
            st.rerun()

    st.divider()

    # Session Management
    col_s1, col_s2 = st.columns(2)
    with col_s1:
        if st.button("🗑️ Clear Chat", use_container_width=True):
            st.session_state.messages = []
            st.session_state.preset_prompt = None
            st.session_state.last_state = None
            st.rerun()
    with col_s2:
        if st.session_state.messages:
            transcript_json = json.dumps(
                [
                    {
                        "role": m.get("role"),
                        "content": m.get("content"),
                        "scores": m.get("evaluation_scores", {}),
                        "mcp": m.get("mcp_result", {}),
                    }
                    for m in st.session_state.messages
                ],
                indent=2,
            )
            st.download_button(
                "📥 Export",
                data=transcript_json,
                file_name="assistant_session.json",
                mime="application/json",
                use_container_width=True,
            )


# --------------------------------------------------
# Main Hero Banner
# --------------------------------------------------
st.markdown(
    """
    <div class="hero-container">
        <div class="hero-title-row">
            <h1 class="hero-title">🤖 Enterprise Knowledge Assistant</h1>
            <div class="live-status-pill">
                <div class="status-dot"></div>
                ORCHESTRATOR ONLINE
            </div>
        </div>
        <div class="hero-subtitle">
            Enterprise-grade autonomous AI assistant orchestrating <b>LangGraph Multi-Agent Workflows</b>, 
            <b>ChromaDB Semantic RAG</b>, <b>RAGAS Automated Quality Evaluation</b>, <b>Presidio PII Guardrails</b>, 
            and <b>FastMCP SQLite Tool Protocol</b>.
        </div>
        <div class="badge-bar">
            <span class="tech-badge">🧠 LangGraph StateGraph</span>
            <span class="tech-badge">🔍 all-MiniLM-L6-v2 Embeddings</span>
            <span class="tech-badge">📚 ChromaDB (64 Chunks)</span>
            <span class="tech-badge">📊 RAGAS 0.4.3 Evaluator</span>
            <span class="tech-badge">🎫 FastMCP Ticket Engine</span>
            <span class="tech-badge">🛡️ Presidio Guardrails</span>
            <span class="tech-badge">👁️ Full Observability</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)


# --------------------------------------------------
# Multi-Tab Navigation
# --------------------------------------------------
tab_chat, tab_observability, tab_knowledge, tab_tickets = st.tabs(
    [
        "💬 Assistant Chat & Actions",
        "🧭 Observability & State Inspector",
        "📚 Knowledge Base Repository",
        "🎫 MCP Ticket Registry",
    ]
)


# ==================================================
# TAB 1: ASSISTANT CHAT & ACTIONS
# ==================================================
with tab_chat:
    # Display message history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

            if message["role"] == "assistant":
                # Observability trace stepper
                if message.get("trace_steps"):
                    steps = message["trace_steps"]
                    steps_html = ' <span class="trace-arrow">➔</span> '.join(
                        f'<span class="trace-node">✓ {s}</span>'
                        for s in steps
                    )
                    st.markdown(
                        f"""
                        <div class="trace-stepper">
                            <span style="font-size:0.75rem; color:#94a3b8; font-weight:700; margin-right:6px;">TRACE PATH:</span>
                            {steps_html}
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                # Retrieved context chunks expander
                if message.get("retrieved_documents"):
                    docs = message["retrieved_documents"]
                    with st.expander(f"📚 Retrieved Contexts ({len(docs)} Document Chunks)", expanded=False):
                        for i, doc in enumerate(docs, 1):
                            source = doc.metadata.get("source", "Knowledge Base") if hasattr(doc, "metadata") else "Knowledge Base"
                            content = doc.page_content if hasattr(doc, "page_content") else str(doc)
                            st.markdown(f"**Chunk #{i}** *(Source: `{source}` | Length: {len(content)} chars)*")
                            st.code(content, language="text")

                # RAGAS Evaluation Results HUD
                if message.get("evaluation_scores"):
                    scores = message["evaluation_scores"]
                    f_val = scores.get("faithfulness", 0.0)
                    r_val = scores.get("answer_relevancy", 0.0)
                    avg_val = (f_val + r_val) / 2.0

                    if avg_val >= 0.8:
                        quality_badge = '<span class="quality-chip-good">🟢 High Quality (Good)</span>'
                    elif avg_val >= 0.6:
                        quality_badge = '<span class="quality-chip-moderate">🟡 Moderate Quality</span>'
                    else:
                        quality_badge = '<span class="quality-chip-low">🔴 Needs Improvement</span>'

                    st.markdown(
                        f"""
                        <div class="ragas-container">
                            <div class="ragas-header">
                                <span class="ragas-title">📊 RAGAS Response Evaluation</span>
                                {quality_badge}
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric(
                            "Faithfulness Score",
                            f"{f_val:.2f}",
                            help="Evaluates whether the response statements are strictly derived from the retrieved context.",
                        )
                        st.progress(max(0.0, min(1.0, float(f_val))))
                    with col2:
                        st.metric(
                            "Answer Relevancy",
                            f"{r_val:.2f}",
                            help="Evaluates how directly the answer addresses the user's question.",
                        )
                        st.progress(max(0.0, min(1.0, float(r_val))))
                    with col3:
                        st.markdown("<div style='font-size: 0.8rem; font-weight:600; color:#94a3b8; margin-bottom:6px;'>EVALUATION SUMMARY</div>", unsafe_allow_html=True)
                        st.caption(message.get("evaluation_summary", "Evaluation complete."))

                # MCP Ticket Card
                if message.get("mcp_result"):
                    mcp_res = message["mcp_result"]
                    if mcp_res.get("success"):
                        t_id = mcp_res.get("ticket_id", "TKT-UNKNOWN")
                        t_title = mcp_res.get("title", "Support Request")
                        t_priority = str(mcp_res.get("priority", "medium")).lower()
                        t_status = str(mcp_res.get("status", "open")).lower()
                        p_class = (
                            "priority-badge-high"
                            if t_priority in ["high", "critical"]
                            else ("priority-badge-medium" if t_priority == "medium" else "priority-badge-low")
                        )

                        st.markdown(
                            f"""
                            <div class="ticket-card">
                                <div class="ticket-header">
                                    <span class="ticket-id">{t_id}</span>
                                    <div>
                                        <span class="{p_class}">{t_priority.upper()} PRIORITY</span>
                                        <span class="status-badge-open">{t_status.upper()}</span>
                                    </div>
                                </div>
                                <div style="font-size: 1.1rem; font-weight: 700; color: #f8fafc; margin-bottom: 6px;">{t_title}</div>
                                <div style="font-size: 0.82rem; color: #94a3b8;">Created via FastMCP Server in SQLite Database.</div>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )
                    else:
                        st.error(f"MCP Ticket Creation Notice: {mcp_res.get('error', 'Operation failed')}")

    # Chat Input Box
    user_query = st.chat_input("Ask a policy question or request an enterprise action (e.g., create a support ticket)...")

    # If triggered via preset button in sidebar
    if st.session_state.preset_prompt:
        user_query = st.session_state.preset_prompt
        st.session_state.preset_prompt = None

    if user_query:
        # Append & display user message
        st.session_state.messages.append({"role": "user", "content": user_query})
        with st.chat_message("user"):
            st.markdown(user_query)

        # Process with LangGraph
        with st.chat_message("assistant"):
            with st.spinner("🤖 Orchestrating Agents (Input Guard ➔ Router ➔ Retriever/MCP ➔ Response ➔ Output Guard ➔ Evaluator)..."):
                initial_state = {
                    "question": user_query,
                    "retrieved_documents": [],
                    "answer": "",
                    "evaluation_scores": {},
                    "evaluation_summary": "",
                    "mcp_action": "",
                    "mcp_result": {},
                }

                try:
                    start_time = time.time()
                    result = graph.invoke(initial_state)
                    elapsed = time.time() - start_time

                    st.session_state.last_state = result

                    answer = result.get("answer", "I could not generate a response.")
                    evaluation_scores = result.get("evaluation_scores", {})
                    evaluation_summary = result.get("evaluation_summary", "")
                    mcp_result = result.get("mcp_result", {})
                    retrieved_docs = result.get("retrieved_documents", [])
                    mcp_action = result.get("mcp_action", "")

                    # Compute execution path
                    trace_steps = ["START", "input_guard", "router"]
                    if mcp_action or mcp_result:
                        trace_steps.extend(["mcp_agent", "fastmcp_server", "END"])
                    else:
                        trace_steps.extend(["retriever_agent", "response_agent", "output_guard", "evaluator_agent", "END"])

                    # Display final answer
                    st.markdown(answer)

                    # Display Trace Stepper
                    steps_html = ' <span class="trace-arrow">➔</span> '.join(
                        f'<span class="trace-node">✓ {s}</span>'
                        for s in trace_steps
                    )
                    st.markdown(
                        f"""
                        <div class="trace-stepper">
                            <span style="font-size:0.75rem; color:#94a3b8; font-weight:700; margin-right:6px;">TRACE PATH:</span>
                            {steps_html}
                            <span style="margin-left:auto; font-size:0.75rem; color:#64748b;">({elapsed:.2f}s)</span>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                    # Retrieved contexts
                    if retrieved_docs:
                        with st.expander(f"📚 Retrieved Contexts ({len(retrieved_docs)} Document Chunks)", expanded=False):
                            for i, doc in enumerate(retrieved_docs, 1):
                                source = doc.metadata.get("source", "Knowledge Base") if hasattr(doc, "metadata") else "Knowledge Base"
                                content = doc.page_content if hasattr(doc, "page_content") else str(doc)
                                st.markdown(f"**Chunk #{i}** *(Source: `{source}` | Length: {len(content)} chars)*")
                                st.code(content, language="text")

                    # RAGAS Evaluation HUD
                    if evaluation_scores:
                        f_val = evaluation_scores.get("faithfulness", 0.0)
                        r_val = evaluation_scores.get("answer_relevancy", 0.0)
                        avg_val = (f_val + r_val) / 2.0

                        if avg_val >= 0.8:
                            quality_badge = '<span class="quality-chip-good">🟢 High Quality (Good)</span>'
                        elif avg_val >= 0.6:
                            quality_badge = '<span class="quality-chip-moderate">🟡 Moderate Quality</span>'
                        else:
                            quality_badge = '<span class="quality-chip-low">🔴 Needs Improvement</span>'

                        st.markdown(
                            f"""
                            <div class="ragas-container">
                                <div class="ragas-header">
                                    <span class="ragas-title">📊 RAGAS Response Evaluation</span>
                                    {quality_badge}
                                </div>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )

                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Faithfulness Score", f"{f_val:.2f}", help="Context grounding score")
                            st.progress(max(0.0, min(1.0, float(f_val))))
                        with col2:
                            st.metric("Answer Relevancy", f"{r_val:.2f}", help="Question relevance score")
                            st.progress(max(0.0, min(1.0, float(r_val))))
                        with col3:
                            st.markdown("<div style='font-size: 0.8rem; font-weight:600; color:#94a3b8; margin-bottom:6px;'>EVALUATION SUMMARY</div>", unsafe_allow_html=True)
                            st.caption(evaluation_summary or "Evaluation complete.")

                    # MCP Ticket Card
                    if mcp_result and mcp_result.get("success"):
                        t_id = mcp_result.get("ticket_id", "TKT-UNKNOWN")
                        t_title = mcp_result.get("title", "Support Request")
                        t_priority = str(mcp_result.get("priority", "medium")).lower()
                        t_status = str(mcp_result.get("status", "open")).lower()
                        p_class = (
                            "priority-badge-high"
                            if t_priority in ["high", "critical"]
                            else ("priority-badge-medium" if t_priority == "medium" else "priority-badge-low")
                        )

                        st.markdown(
                            f"""
                            <div class="ticket-card">
                                <div class="ticket-header">
                                    <span class="ticket-id">{t_id}</span>
                                    <div>
                                        <span class="{p_class}">{t_priority.upper()} PRIORITY</span>
                                        <span class="status-badge-open">{t_status.upper()}</span>
                                    </div>
                                </div>
                                <div style="font-size: 1.1rem; font-weight: 700; color: #f8fafc; margin-bottom: 6px;">{t_title}</div>
                                <div style="font-size: 0.82rem; color: #94a3b8;">Created via FastMCP Server in SQLite Database.</div>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )

                    # Save to session
                    st.session_state.messages.append(
                        {
                            "role": "assistant",
                            "content": answer,
                            "evaluation_scores": evaluation_scores,
                            "evaluation_summary": evaluation_summary,
                            "mcp_result": mcp_result,
                            "retrieved_documents": retrieved_docs,
                            "trace_steps": trace_steps,
                        }
                    )

                except Exception as exc:
                    err_str = str(exc)
                    if "PII" in err_str or "Validation failed" in err_str or "Guardrail" in err_str:
                        err_msg = "🛡️ **Security Guardrail Triggered**: Your request contains sensitive personal details (such as an email or phone number) and was safely blocked by the enterprise guardrail before sending to the model."
                        st.warning(err_msg)
                        st.session_state.messages.append(
                            {
                                "role": "assistant",
                                "content": err_msg,
                                "trace_steps": ["START", "input_guard (BLOCKED)"],
                            }
                        )
                    else:
                        # Fallback to direct retrieval & grounded answer
                        try:
                            from rag.retriever import KnowledgeRetriever
                            from langchain_ollama import ChatOllama
                            retriever = KnowledgeRetriever()
                            fallback_docs = retriever.retrieve(user_query)
                            context = "\n\n".join(d.page_content for d in fallback_docs[:3])
                            llm = ChatOllama(model="gpt-oss:120b-cloud", temperature=0)
                            prompt = f"Answer the user question concisely using ONLY the context:\n\nContext:\n{context}\n\nQuestion:\n{user_query}\n\nAnswer:"
                            res = llm.invoke(prompt)
                            fallback_answer = res.content
                            st.markdown(fallback_answer)
                            st.session_state.messages.append(
                                {
                                    "role": "assistant",
                                    "content": fallback_answer,
                                    "retrieved_documents": fallback_docs[:3],
                                    "trace_steps": ["START", "retriever", "response", "END"],
                                }
                            )
                        except Exception:
                            err_msg = f"⚠️ Could not complete request: {err_str}"
                            st.error(err_msg)
                            st.session_state.messages.append(
                                {
                                    "role": "assistant",
                                    "content": err_msg,
                                }
                            )


# ==================================================
# TAB 2: OBSERVABILITY & STATE INSPECTOR
# ==================================================
with tab_observability:
    st.markdown("### 🧭 LangGraph Observability & Multi-Agent State Inspector")
    st.caption("Inspect live graph execution state, node latency, and agent routing paths.")

    col_o1, col_o2 = st.columns([1, 1])

    with col_o1:
        st.markdown("#### 📐 Active Graph Architecture")
        st.markdown(
            """
            ```mermaid
            graph TD
                START([START]) --> InputGuard[🛡️ input_guard]
                InputGuard --> Router{🔀 router}
                Router -->|Knowledge Query| Retriever[🔍 retriever_agent]
                Retriever --> Response[🤖 response_agent]
                Response --> OutputGuard[🛡️ output_guard]
                OutputGuard --> Evaluator[📊 evaluator_agent]
                Evaluator --> END_K([END])
                Router -->|Action Request| MCPAgent[🎫 mcp_agent]
                MCPAgent --> FastMCP[⚙️ fastmcp_server / SQLite]
                FastMCP --> END_A([END])
            ```
            """
        )

    with col_o2:
        st.markdown("#### 🔍 Latest GraphState Snapshot")
        if st.session_state.last_state:
            state_data = {
                "question": st.session_state.last_state.get("question"),
                "retrieved_documents_count": len(st.session_state.last_state.get("retrieved_documents", [])),
                "answer_length": len(st.session_state.last_state.get("answer", "")),
                "evaluation_scores": st.session_state.last_state.get("evaluation_scores", {}),
                "evaluation_summary": st.session_state.last_state.get("evaluation_summary", ""),
                "mcp_action": st.session_state.last_state.get("mcp_action", ""),
                "mcp_result": st.session_state.last_state.get("mcp_result", {}),
            }
            st.json(state_data)
        else:
            st.info("No queries executed yet in this session. Run a query from the Chat tab to inspect live StateGraph data.")

    st.markdown("---")
    st.markdown("#### 🛡️ Active Guardrail Rules (Microsoft Presidio + Regex Engine)")
    st.markdown(
        """
        | Entity Type | Detection Mechanism | Action Upon Detection |
        |---|---|---|
        | **Email Address** | Presidio `EmailRecognizer` + RFC Regex | Block input before LLM invocation |
        | **Phone Number** | Presidio `PhoneRecognizer` | Block input before LLM invocation |
        | **Credit Card** | Presidio `CreditCardRecognizer` (Luhn Validated) | Block input before LLM invocation |
        | **National ID (SSN / PAN / Aadhaar)** | Custom Regex Pattern Registry | Block input before LLM invocation |
        | **IP Address & Secrets** | Presidio `IpRecognizer` | Mask/Block before LLM invocation |
        """
    )


# ==================================================
# TAB 3: KNOWLEDGE BASE REPOSITORY
# ==================================================
with tab_knowledge:
    st.markdown("### 📚 Enterprise Knowledge Base Repository")
    st.caption("Explore verified policy documents currently indexed into the ChromaDB vector database.")

    kb_dir = Path("knowledge_base/general")
    if kb_dir.exists():
        files = sorted(list(kb_dir.glob("*.txt")))

        search_term = st.text_input("🔍 Filter Knowledge Documents by keyword:", "")

        for doc_file in files:
            doc_text = doc_file.read_text(encoding="utf-8")
            if not search_term or search_term.lower() in doc_text.lower() or search_term.lower() in doc_file.name.lower():
                with st.expander(f"📄 {doc_file.name.replace('_', ' ').replace('.txt', '').title()} (`{doc_file.name}`)", expanded=False):
                    st.caption(f"File Path: `{doc_file}` | Characters: {len(doc_text)}")
                    st.text(doc_text)
    else:
        st.warning("Knowledge base directory `knowledge_base/general` not found.")


# ==================================================
# TAB 4: MCP TICKET REGISTRY
# ==================================================
with tab_tickets:
    st.markdown("### 🎫 FastMCP Enterprise Ticket Registry")
    st.caption("Live view of support tickets stored in the SQLite database via FastMCP tools.")

    tickets = get_sqlite_tickets()

    col_t1, col_t2 = st.columns([3, 1])
    with col_t1:
        st.markdown(f"**Total Registered Tickets:** `{len(tickets)}`")
    with col_t2:
        if st.button("🔄 Refresh Tickets", use_container_width=True):
            st.rerun()

    if tickets:
        for t in tickets:
            t_id = f"TKT-{t['id']:04d}"
            t_prio = str(t["priority"]).lower()
            p_class = (
                "priority-badge-high"
                if t_prio in ["high", "critical"]
                else ("priority-badge-medium" if t_prio == "medium" else "priority-badge-low")
            )

            st.markdown(
                f"""
                <div class="ticket-card" style="margin-bottom: 12px;">
                    <div class="ticket-header">
                        <span class="ticket-id">{t_id}</span>
                        <div>
                            <span class="{p_class}">{t_prio.upper()}</span>
                            <span class="status-badge-open">{str(t['status']).upper()}</span>
                        </div>
                    </div>
                    <div style="font-size: 1.05rem; font-weight: 700; color: #f8fafc;">{t['title']}</div>
                    <div style="font-size: 0.88rem; color: #cbd5e1; margin-top: 6px;">{t['description']}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
    else:
        st.info("No tickets created yet. Use the chat interface to say: *'Create a high priority support ticket because VPN is down'*.")