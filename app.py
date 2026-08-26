import time

import streamlit as st

from copilot_service import CopilotService


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Copilot Developer Agent",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# SESSION STATE
# ============================================================

defaults = {
    "copilot_service": None,
    "connected": False,
    "messages": [],
    "repository_path": (
        r"C:\Users\satya\Downloads\github_copilot"
        r"\repositories\enterprise_knowledge_assistant"
    ),
    "auth_mode": "Existing Copilot Login",
    "persona": "Developer",
    "last_operation_status": None,
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value


# ============================================================
# CSS
# ============================================================

st.markdown(
    """
    <style>

    .stApp {
        background-color: #0e1117;
    }

    section[data-testid="stSidebar"] {
        background-color: #161b22;
    }

    .app-title {
        font-size: 32px;
        font-weight: 700;
    }

    .app-subtitle {
        color: #8b949e;
        font-size: 15px;
        margin-bottom: 25px;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.markdown("## 🤖 Copilot Agent")
    st.caption("Developer workspace")

    st.divider()

    # ========================================================
    # AUTHENTICATION
    # ========================================================

    st.markdown("### Authentication")

    auth_mode = st.radio(
        "Authentication method",
        [
            "Existing Copilot Login",
            "GitHub Token",
        ],
        label_visibility="collapsed",
    )

    github_token = None

    if auth_mode == "GitHub Token":

        github_token = st.text_input(
            "GitHub PAT",
            type="password",
            placeholder="github_pat_...",
            help=(
                "Use a token with the required Copilot "
                "permission when authenticating through a PAT."
            ),
        )

        st.caption(
            "The token is used only for the current session."
        )

    else:

        st.caption(
            "Uses your existing Copilot authentication."
        )

    st.divider()

    # ========================================================
    # LOCAL REPOSITORY
    # ========================================================

    st.markdown("### Local Repository")

    repository_path = st.text_input(
        "Repository path",
        value=st.session_state.repository_path,
        placeholder=r"C:\path\to\repository",
        label_visibility="collapsed",
    )

    st.caption(
        "The agent works directly against this local path."
    )

    st.divider()

    # ========================================================
    # PERSONA
    # ========================================================

    st.markdown("### Persona")

    persona = st.selectbox(
        "Agent persona",
        ["Developer"],
        label_visibility="collapsed",
    )

    st.divider()

    # ========================================================
    # CONNECT
    # ========================================================

    if st.button(
        "🔌 Connect",
        use_container_width=True,
        type="primary",
    ):

        if not repository_path.strip():

            st.error(
                "Repository path cannot be empty."
            )

        elif (
            auth_mode == "GitHub Token"
            and not github_token
        ):

            st.error(
                "Please enter your GitHub PAT."
            )

        else:

            try:

                old_service = (
                    st.session_state.copilot_service
                )

                if old_service:

                    try:
                        old_service.stop()
                    except Exception:
                        pass

                service = CopilotService()

                service.start(
                    github_token=(
                        github_token.strip()
                        if github_token
                        else None
                    ),
                    repository_path=(
                        repository_path.strip()
                    ),
                )

                st.session_state.copilot_service = service
                st.session_state.connected = True
                st.session_state.repository_path = (
                    repository_path.strip()
                )
                st.session_state.auth_mode = auth_mode
                st.session_state.persona = persona
                st.session_state.messages = []
                st.session_state.last_operation_status = None

                st.success(
                    "Copilot connected successfully."
                )

            except Exception as e:

                st.session_state.connected = False
                st.session_state.copilot_service = None

                st.error(
                    f"Connection failed: {e}"
                )

    # ========================================================
    # STATUS
    # ========================================================

    st.markdown("### Status")

    if st.session_state.connected:
        st.success("● Connected")
    else:
        st.error("● Not connected")


# ============================================================
# HEADER
# ============================================================

st.markdown(
    '<div class="app-title">'
    "Copilot Developer Agent"
    "</div>",
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="app-subtitle">'
    "AI-powered development assistant for your repository"
    "</div>",
    unsafe_allow_html=True,
)


# ============================================================
# NOT CONNECTED
# ============================================================

if not st.session_state.connected:

    st.info(
        "Connect Copilot and select a local repository "
        "to start."
    )

    st.stop()


# ============================================================
# SERVICE
# ============================================================

service = st.session_state.copilot_service


if service is None:

    st.error(
        "Copilot service is unavailable. Please reconnect."
    )

    st.stop()


# ============================================================
# REPOSITORY / PERSONA
# ============================================================

repo_col, persona_col = st.columns(2)

with repo_col:

    st.subheader("📁 Repository")

    st.code(
        st.session_state.repository_path
    )

with persona_col:

    st.subheader("👨‍💻 Persona")

    st.info(
        st.session_state.persona
    )


# ============================================================
# OPERATION STATUS
# ============================================================

if (
    st.session_state.last_operation_status
    == "approved"
):

    st.success(
        "✅ Operation approved. The agent is completing it."
    )

elif (
    st.session_state.last_operation_status
    == "rejected"
):

    st.error(
        "❌ Operation declined. The operation was not performed."
    )


# ============================================================
# HITL APPROVAL
# ============================================================

pending = service.get_pending_approval()

if pending:

    tool_name = pending.get(
        "tool",
        "Unknown",
    )

    arguments = pending.get(
        "arguments",
        {},
    )

    st.warning(
        "⚠️ Human Approval Required"
    )

    st.info(
        "The Developer Agent wants to perform an "
        "operation that requires your approval."
    )

    st.markdown(
        f"**Tool:** `{tool_name}`"
    )

    st.markdown(
        "**Arguments / Command:**"
    )

    st.code(
        str(arguments),
        language="json",
    )

    st.warning(
        "Review this operation carefully before approving it."
    )

    approve_col, reject_col = st.columns(2)

    with approve_col:

        if st.button(
            "✓ Approve",
            type="primary",
            use_container_width=True,
            key="hitl_approve",
        ):

            if service.approve():

                st.session_state.last_operation_status = (
                    "approved"
                )

                st.rerun()

            else:

                st.error(
                    "No pending approval found."
                )

    with reject_col:

        if st.button(
            "✕ Reject",
            use_container_width=True,
            key="hitl_reject",
        ):

            if service.reject():

                st.session_state.last_operation_status = (
                    "rejected"
                )

                st.rerun()

            else:

                st.error(
                    "No pending approval found."
                )


# ============================================================
# AGENT STATE
# ============================================================

agent_state = service.get_agent_state()


# ============================================================
# RESULT AVAILABLE
# ============================================================

if (
    not agent_state["running"]
    and agent_state["result"] is not None
):

    result = agent_state["result"]

    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": result,
        }
    )

    service.clear_agent_result()

    st.rerun()


# ============================================================
# ERROR AVAILABLE
# ============================================================

if (
    not agent_state["running"]
    and agent_state["error"] is not None
):

    error = agent_state["error"]

    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": (
                "⚠️ **Agent error**\n\n"
                f"{error}"
            ),
        }
    )

    service.clear_agent_result()

    st.rerun()


# ============================================================
# CHAT HISTORY
# ============================================================

for message in st.session_state.messages:

    with st.chat_message(
        message["role"]
    ):

        st.markdown(
            message["content"]
        )


# ============================================================
# AGENT WORKING
# ============================================================

agent_state = service.get_agent_state()

if agent_state["running"]:

    if service.get_pending_approval():

        st.info(
            "🤖 The agent is waiting for your approval above."
        )

    else:

        st.info(
            "🤖 Developer Agent is working..."
        )

    time.sleep(0.8)

    st.rerun()


# ============================================================
# CHAT INPUT
# ============================================================

if not agent_state["running"]:

    prompt = st.chat_input(
        "Ask your Developer Agent..."
    )

    if prompt:

        # Add user's message immediately.
        st.session_state.messages.append(
            {
                "role": "user",
                "content": prompt,
            }
        )

        # Clear previous operation status.
        st.session_state.last_operation_status = None

        # Start the request in CopilotService.
        started = service.ask_background(
            prompt
        )

        if not started:

            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "content": (
                        "⚠️ Another request is already "
                        "being processed."
                    ),
                }
            )

        st.rerun()
