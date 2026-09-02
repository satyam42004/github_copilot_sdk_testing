import time
from pathlib import Path

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
        r"C:\Users\satya\Desktop\copilot_empty_test"
    ),
    "auth_mode": "Existing Copilot Login",
    "persona": "Developer",
    "last_operation_status": None,
    "uploaded_files": [],
    "allowed_folders": [],
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
    # FILE UPLOAD
    # ========================================================

    st.markdown("### Attach Files")

    uploaded_files = st.file_uploader(
        "Upload files for the agent",
        accept_multiple_files=True,
        type=[
            "txt", "md", "py", "js", "ts", "tsx", "jsx",
            "html", "css", "json", "yaml", "yml", "xml",
            "csv", "sql", "java", "c", "cpp", "h", "hpp",
            "go", "rs", "sh", "ps1", "pdf",
        ],
        help="Attach text/code files or PDFs to the next agent request.",
        label_visibility="collapsed",
    )

    if uploaded_files:
        st.session_state.uploaded_files = uploaded_files
        st.caption(f"{len(uploaded_files)} file(s) attached")

        for file in uploaded_files:
            st.write(f"📎 {file.name}")

    elif st.session_state.uploaded_files:
        st.session_state.uploaded_files = []

    st.divider()

    # ========================================================
    # OBSERVABILITY
    # ========================================================

    st.markdown("### Observability")

    col1, col2 = st.columns(2)

    with col1:
        if st.button(
            "📊 Open Phoenix Traces",
            use_container_width=True,
        ):
            st.info(
                "Opening Phoenix at http://localhost:6006"
            )

    with col2:
        if st.button(
            "🔄 Refresh Traces",
            use_container_width=True,
        ):
            st.info(
                "Traces update automatically in Phoenix"
            )

    st.caption(
        "Phoenix traces at: http://localhost:6006"
    )

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
        "The repository is always included in the access policy."
    )

    # ========================================================
    # FILE ACCESS POLICY
    # ========================================================

    st.markdown("### File Access")

    desktop_path = str(Path.home() / "Desktop")

    default_allowed_folders = (
        st.session_state.allowed_folders
        or [desktop_path]
    )

    allowed_folders_text = st.text_area(
        "Additional allowed folders",
        value="\n".join(default_allowed_folders),
        help=(
            "Enter one folder per line. The repository is always "
            "allowed. These folders are additional locations the "
            "agent is allowed to access."
        ),
        height=100,
        label_visibility="collapsed",
    )

    st.caption(
        "Default: Repository + Desktop. "
        "Downloads/Documents remain blocked unless explicitly added."
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

                # One folder per line.
                configured_allowed_folders = [
                    line.strip()
                    for line in allowed_folders_text.splitlines()
                    if line.strip()
                ]

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
                    allowed_folders=(
                        configured_allowed_folders
                    ),
                )

                st.session_state.copilot_service = service
                st.session_state.connected = True
                st.session_state.repository_path = (
                    repository_path.strip()
                )
                st.session_state.auth_mode = auth_mode
                st.session_state.persona = persona
                st.session_state.allowed_folders = (
                    configured_allowed_folders
                )
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
    # COPILOT USAGE
    # ========================================================

    st.divider()
    st.markdown("### Copilot Usage")

    if st.session_state.copilot_service is not None:

        usage = st.session_state.copilot_service.get_usage()

        st.metric(
            "AI Credits",
            f"{usage['ai_credits']:.2f}",
        )

        st.caption(f"Model: {usage['model']}")
        st.caption(f"Session model calls: {usage['assistant_calls']}")

        usage_col1, usage_col2 = st.columns(2)

        with usage_col1:
            st.metric("Input Tokens", f"{usage['input_tokens']:,}")
            st.metric("Cache Read", f"{usage['cache_read_tokens']:,}")
            st.metric("Reasoning", f"{usage['reasoning_tokens']:,}")

        with usage_col2:
            st.metric("Output Tokens", f"{usage['output_tokens']:,}")
            st.metric("Cache Write", f"{usage['cache_write_tokens']:,}")
            st.metric("Total Tokens", f"{usage['total_tokens']:,}")

        st.caption(
            f"Total nano AIU: {usage['total_nano_aiu']:,.0f}"
        )

        current = usage.get("current_request")
        completed = usage.get("last_completed_request")

        st.markdown("#### Current Request")

        if current:
            st.write(f"**Request ID:** `{current['request_id']}`")
            st.write(f"**Status:** `{current['status']}`")
            req_col1, req_col2 = st.columns(2)
            with req_col1:
                st.metric("Request Input", f"{current['input_tokens']:,}")
                st.metric("HITL Approvals", current["hitl_approvals"])
                st.metric("Tools Started", current["tools_started"])
            with req_col2:
                st.metric("Request Output", f"{current['output_tokens']:,}")
                st.metric("HITL Rejections", current["hitl_rejections"])
                st.metric("Tools Succeeded", current["tools_succeeded"])
            st.caption(
                f"Request Total: {current['total_tokens']:,} | "
                f"Model calls: {current['assistant_calls']} | "
                f"Tools failed: {current['tools_failed']}"
            )
        else:
            st.caption("No request currently running.")

        st.markdown("#### Last Completed Request")

        if completed:
            st.write(f"**Request ID:** `{completed['request_id']}`")
            st.write(f"**Status:** `{completed['status']}`")
            st.caption(
                f"Model: {completed['model']} | "
                f"Input: {completed['input_tokens']:,} | "
                f"Output: {completed['output_tokens']:,} | "
                f"Total: {completed['total_tokens']:,}"
            )
            st.caption(
                f"AI credits: {completed['ai_credits']:.2f} | "
                f"HITL approvals: {completed['hitl_approvals']} | "
                f"HITL rejections: {completed['hitl_rejections']} | "
                f"Tools: {completed['tools_started']} started / "
                f"{completed['tools_succeeded']} succeeded / "
                f"{completed['tools_failed']} failed"
            )
        else:
            st.caption("No completed request yet.")

    # ========================================================
    # ACTIVE FILE ACCESS
    # ========================================================

    if st.session_state.copilot_service is not None:

        policy = (
            st.session_state.copilot_service
            .get_file_access_policy()
        )

        st.divider()

        st.markdown("### Allowed File Access")

        st.caption(
            "Read / Write folders:"
        )

        for folder in policy.get("write", []):

            st.code(
                folder,
                language=None,
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
# SAVE UPLOADED FILES
# ============================================================

def save_uploaded_files(
    files,
    repository_path,
):
    """Save uploads into a repository-local folder.

    This is application-controlled storage, not an agent tool
    operation. The repository itself is part of the configured
    access policy.
    """

    if not files:
        return []

    upload_dir = (
        Path(repository_path)
        / "uploaded_files"
    )

    upload_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    saved_files = []

    for file in files:

        # Prevent path components in the uploaded filename.
        filename = Path(file.name).name

        destination = (
            upload_dir / filename
        )

        # Never overwrite an existing upload.
        if destination.exists():

            stem = destination.stem
            suffix = destination.suffix
            counter = 1

            while destination.exists():

                destination = (
                    upload_dir
                    / f"{stem}_{counter}{suffix}"
                )

                counter += 1

        destination.write_bytes(
            file.getvalue()
        )

        saved_files.append(
            str(destination)
        )

    return saved_files


# ============================================================
# FILE CONTENT EXTRACTION
# ============================================================

def extract_uploaded_file(file):
    """Extract readable text from an uploaded file."""

    suffix = Path(
        file.name
    ).suffix.lower()

    data = file.getvalue()

    if suffix == ".pdf":

        try:

            from pypdf import PdfReader
            import io

            reader = PdfReader(
                io.BytesIO(data)
            )

            pages = []

            for page in reader.pages:

                pages.append(
                    page.extract_text()
                    or ""
                )

            return "\n\n".join(
                pages
            ).strip()

        except ImportError:

            return (
                f"[PDF extraction unavailable for {file.name}. "
                "Install pypdf with: uv add pypdf]"
            )

        except Exception as exc:

            return (
                f"[Could not read PDF {file.name}: {exc}]"
            )

    try:

        return data.decode(
            "utf-8"
        )

    except UnicodeDecodeError:

        return (
            f"[Binary/non-UTF-8 file: {file.name}. "
            "The file was uploaded but its contents "
            "could not be decoded as text.]"
        )


def build_prompt_with_files(
    prompt,
    files,
):
    """Build the agent prompt with attached file contents."""

    if not files:
        return prompt

    sections = [
        prompt,
        "",
        "ATTACHED USER FILES:",
        "The following files were explicitly uploaded by the user.",
        "Use them as additional context for this request.",
        "Do not assume their contents beyond what is provided below.",
    ]

    for file in files:

        content = extract_uploaded_file(
            file
        )

        # Keep the current safety limit for now.
        # Token optimization will be handled as a separate task.
        max_chars = 100_000

        if len(content) > max_chars:

            content = (
                content[:max_chars]
                + "\n\n"
                "[Content truncated at 100,000 characters.]"
            )

        sections.extend(
            [
                "",
                f"--- FILE: {file.name} ---",
                content,
                f"--- END FILE: {file.name} ---",
            ]
        )

    return "\n".join(
        sections
    )


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

service = (
    st.session_state.copilot_service
)

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
        "❌ Operation declined or blocked. "
        "The operation was not performed."
    )


# ============================================================
# HITL APPROVAL
# ============================================================

pending = (
    service.get_pending_approval()
)

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

    approve_col, reject_col = (
        st.columns(2)
    )

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

agent_state = (
    service.get_agent_state()
)


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

agent_state = (
    service.get_agent_state()
)

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

        st.session_state.messages.append(
            {
                "role": "user",
                "content": prompt,
            }
        )

        st.session_state.last_operation_status = None

        saved_files = save_uploaded_files(
            st.session_state.uploaded_files,
            st.session_state.repository_path,
        )

        if saved_files:

            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "content": (
                        "📁 **Uploaded file(s) saved:**\n\n"
                        + "\n".join(
                            f"- `{path}`"
                            for path in saved_files
                        )
                    ),
                }
            )

        request_prompt = (
            build_prompt_with_files(
                prompt,
                st.session_state.uploaded_files,
            )
        )

        started = (
            service.ask_background(
                request_prompt
            )
        )

        st.session_state.uploaded_files = []

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
