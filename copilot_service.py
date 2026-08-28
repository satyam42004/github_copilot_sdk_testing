import asyncio
import json
import threading
from pathlib import Path

from copilot import CopilotClient
from copilot.session_events import SessionEventType

from tools import list_files, read_file, search_code

from observability import (
    configure_tracing,
    optional_span,
    record_event_span,
    flush_traces,
)


# ==========================================================
# USAGE TRACKER
# ==========================================================

class UsageTracker:
    """Tracks Copilot SDK token and AI-credit usage."""

    def __init__(self):
        self.reset()

    def reset(self):
        self.model = None
        self.input_tokens = 0
        self.output_tokens = 0
        self.cache_read_tokens = 0
        self.cache_write_tokens = 0
        self.reasoning_tokens = 0
        self.ai_credits = 0.0
        self.total_nano_aiu = 0.0
        self.assistant_calls = 0

    def handle_event(self, event):
        """Handle Copilot SDK usage events."""

        if event.type == SessionEventType.ASSISTANT_USAGE:
            data = event.data

            self.model = data.model
            self.input_tokens += data.input_tokens or 0
            self.output_tokens += data.output_tokens or 0
            self.cache_read_tokens += data.cache_read_tokens or 0
            self.cache_write_tokens += data.cache_write_tokens or 0
            self.reasoning_tokens += data.reasoning_tokens or 0
            self.assistant_calls += 1

            # Keep the latest per-call cost for visibility.
            # The session checkpoint below is authoritative
            # for the accumulated session-level AI credits.
            if data.cost is not None:
                self.ai_credits = data.cost

            record_event_span(
                "copilot.usage",
                {
                    "gen_ai.request.model": data.model or "unknown",
                    "gen_ai.usage.input_tokens": data.input_tokens or 0,
                    "gen_ai.usage.output_tokens": data.output_tokens or 0,
                    "copilot.usage.cache_read_tokens": data.cache_read_tokens or 0,
                    "copilot.usage.cache_write_tokens": data.cache_write_tokens or 0,
                    "copilot.usage.reasoning_tokens": data.reasoning_tokens or 0,
                    "copilot.usage.ai_credits": data.cost or 0,
                },
            )

            print("\n" + "-" * 60)
            print("ASSISTANT USAGE")
            print("-" * 60)
            print(f"Model:              {data.model}")
            print(f"Input tokens:       {data.input_tokens}")
            print(f"Output tokens:      {data.output_tokens}")
            print(f"Cache read tokens:  {data.cache_read_tokens}")
            print(f"Cache write tokens: {data.cache_write_tokens}")
            print(f"Reasoning tokens:   {data.reasoning_tokens}")
            print(f"AI credits:         {data.cost}")

        elif event.type == SessionEventType.SESSION_USAGE_CHECKPOINT:
            data = event.data

            self.total_nano_aiu = getattr(
                data, "total_nano_aiu", 0
            ) or 0

            # SDK 1.0.11 exposes the accumulated session value
            # as _total_premium_requests.
            session_credits = getattr(
                data, "_total_premium_requests", None
            )

            if session_credits is not None:
                self.ai_credits = session_credits

    def get_usage(self):
        """Return current session usage for Streamlit/UI."""
        return {
            "model": self.model or "unknown",
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "total_tokens": self.input_tokens + self.output_tokens,
            "cache_read_tokens": self.cache_read_tokens,
            "cache_write_tokens": self.cache_write_tokens,
            "reasoning_tokens": self.reasoning_tokens,
            "ai_credits": self.ai_credits,
            "total_nano_aiu": self.total_nano_aiu,
            "assistant_calls": self.assistant_calls,
        }


class CopilotService:
    """Persistent Copilot SDK service with repository access,
    HITL and Phoenix tracing.
    """

    def __init__(self):

        self.client = None
        self.session = None
        self.repository_path = None

        # Copilot SDK usage / AI-credit tracking.
        self.usage_tracker = UsageTracker()

        # Persistent asyncio loop.
        self.loop = None
        self.loop_thread = None
        self.ready = threading.Event()

        # HITL state.
        self.approval_required = False
        self.pending_tool = None
        self.pending_arguments = None
        self.approval_result = None
        self.approval_event = None

        # Agent state.
        self.agent_running = False
        self.agent_result = None
        self.agent_error = None

        # Operation state.
        self.last_approval_decision = None
        self.last_approved_tool = None
        self.last_approved_arguments = None
        self.last_denied_operation = None

    # ==========================================================
    # ASYNC LOOP
    # ==========================================================

    def _run_loop(self):

        self.loop = asyncio.new_event_loop()

        asyncio.set_event_loop(
            self.loop
        )

        self.ready.set()

        self.loop.run_forever()

    def _ensure_loop(self):

        if (
            self.loop is None
            or self.loop_thread is None
            or not self.loop_thread.is_alive()
        ):

            self.ready.clear()

            self.loop_thread = threading.Thread(
                target=self._run_loop,
                daemon=True,
            )

            self.loop_thread.start()

            self.ready.wait()

    # ==========================================================
    # START
    # ==========================================================

    def start(
        self,
        github_token: str | None,
        repository_path: str,
    ):

        # IMPORTANT:
        # Streamlit calls this service from its own process.
        # Initialize Phoenix before creating the Copilot session.

        configure_tracing()
        self.usage_tracker.reset()

        self._ensure_loop()

        future = (
            asyncio.run_coroutine_threadsafe(
                self._async_start(
                    github_token=github_token,
                    repository_path=repository_path,
                ),
                self.loop,
            )
        )

        return future.result()

    async def _async_start(
        self,
        github_token,
        repository_path,
    ):

        repository = (
            Path(repository_path)
            .expanduser()
            .resolve()
        )

        if not repository.exists():

            raise ValueError(
                f"Repository does not exist:\n"
                f"{repository}"
            )

        if not repository.is_dir():

            raise ValueError(
                f"Repository path is not a directory:\n"
                f"{repository}"
            )

        self.repository_path = repository

        # ------------------------------------------------------
        # Copilot session span
        # ------------------------------------------------------

        with optional_span(
            "copilot.session.start",
            {
                "copilot.repository":
                    str(repository),

                "copilot.auth_mode":
                    (
                        "github_token"
                        if github_token
                        else "existing_login"
                    ),
            },
        ):

            if github_token:

                self.client = CopilotClient(
                    github_token=
                        github_token.strip(),

                    use_logged_in_user=False,
                )

            else:

                self.client = CopilotClient(
                    use_logged_in_user=True,
                )

            await self.client.start()

            repository_context = f"""
CURRENT LOCAL REPOSITORY:
{repository}

The configured local repository is the source of truth for
repository questions.

Local filesystem access does not by itself prove GitHub
remote permissions.
"""

            self.session = (
                await self.client.create_session(

                    model="auto",

                    working_directory=
                        str(repository),

                    tools=[
                        list_files,
                        read_file,
                        search_code,
                    ],

                    # Capture Copilot SDK usage events so the
                    # Streamlit app has the same usage data as CLI.
                    on_event=self.usage_tracker.handle_event,

                    hooks={

                        "on_pre_tool_use":
                            self._pre_tool_use,

                        "on_post_tool_use":
                            self._post_tool_use,

                        "on_post_tool_use_failure":
                            self._post_tool_use_failure,
                    },

                    system_message={

                        "mode": "append",

                        "content":
                            repository_context
                            + """

You are a Senior Software Developer.

GENERAL CONVERSATION:
- Answer greetings and general questions normally.
- Do not call repository tools for simple greetings.

REPOSITORY TOOL POLICY:
- For repository questions, use the available custom
  repository tools whenever actual repository information
  is required.
- Never invent repository files, technologies, architecture,
  classes, functions, or configuration.
- Use list_files for repository structure.
- Use read_file to inspect files.
- Use search_code to find code, symbols, or references.
- Prefer these custom repository tools over shell commands
  whenever they are sufficient.
- Do not use PowerShell as a substitute for a custom
  repository tool when a custom tool can answer the request.

TOOL SELECTION:
- Repository structure -> list_files
- File contents -> read_file
- Code or symbol search -> search_code
- Use another tool only when the custom tools cannot
  perform the requested operation.

SAFETY:
- Read-only operations are low risk.
- File creation, modification, deletion, commits,
  pushes, and destructive commands require HITL approval.
- Never bypass HITL approval.
- Never retry a rejected operation.
- Never claim a modification succeeded unless it actually did.
- Never expose tokens, credentials, or secrets.

PERSONA:
- Be concise, practical, technically accurate and clear.
- Distinguish facts from assumptions.
"""
                    },
                )
            )

        print(
            "[OK] Copilot session created."
        )

        print(
            "[OK] Custom repository tools configured."
        )

        record_event_span(
            "copilot.session.ready",
            {
                "repository":
                    str(repository),

                "custom_tools":
                    "list_files,read_file,search_code",
            },
        )

        flush_traces()

    # ==========================================================
    # USAGE
    # ==========================================================

    def get_usage(self):
        """Return current Copilot session usage."""
        return self.usage_tracker.get_usage()

    # ==========================================================
    # REPOSITORY STATUS
    # ==========================================================

    def get_repository_status(self):

        if not self.repository_path:

            return {
                "accessible": False,
                "path": None,
                "message":
                    "No repository is configured.",
            }

        repository = Path(
            self.repository_path
        )

        accessible = (
            repository.exists()
            and repository.is_dir()
        )

        return {
            "accessible":
                accessible,

            "path":
                str(repository),

            "message": (
                "Local repository is accessible."
                if accessible
                else
                "Local repository is not accessible."
            ),
        }

    # ==========================================================
    # RISK CLASSIFICATION
    # ==========================================================

    def _classify_tool(
        self,
        tool_name,
        tool_args,
    ):

        read_only_tools = {
            "list_files",
            "read_file",
            "search_code",
        }

        if tool_name in read_only_tools:
            return "LOW"

        if tool_name in {
            "create",
            "write",
            "write_file",
            "edit",
            "delete",
            "remove",
            "git_commit",
            "git_push",
        }:
            return "HIGH"

        if tool_name == "powershell":

            try:

                parsed = (
                    json.loads(tool_args)
                    if isinstance(
                        tool_args,
                        str,
                    )
                    else tool_args
                )

                command = str(
                    parsed.get(
                        "command",
                        "",
                    )
                ).strip()

            except Exception:

                command = str(
                    tool_args
                )

            command_lower = (
                command.lower().strip()
            )

            destructive_commands = [
                "remove-item",
                "del ",
                "erase ",
                "rmdir",
                "format-",
                "clear-content",
                "set-content",
                "add-content",
                "out-file",
                "new-item",
                "move-item",
                "copy-item",
                "git push",
                "git reset --hard",
                "git clean",
                "git checkout --",
                "git restore",
            ]

            if any(
                keyword in command_lower
                for keyword in destructive_commands
            ):

                return "HIGH"

            read_only_commands = [
                "get-childitem",
                "get-content",
                "select-string",
                "get-location",
                "get-item",
                "test-path",
                "get-filehash",
                "git status",
                "git log",
                "git branch",
                "git diff",
                "git show",
            ]

            if any(
                command_lower.startswith(command)
                for command in read_only_commands
            ):

                return "LOW"

            return "MEDIUM"

        return "MEDIUM"

    # ==========================================================
    # PRE TOOL
    # ==========================================================

    async def _pre_tool_use(
        self,
        input_data,
        invocation,
    ):

        tool_name = input_data.get(
            "toolName",
            "unknown",
        )

        tool_args = input_data.get(
            "toolArgs",
            {},
        )

        risk_level = (
            self._classify_tool(
                tool_name,
                tool_args,
            )
        )

        # ------------------------------------------------------
        # LOW RISK
        # ------------------------------------------------------

        if risk_level == "LOW":

            with optional_span(
                "copilot.tool.approval",
                {
                    "tool.name":
                        tool_name,

                    "tool.risk":
                        risk_level,

                    "hitl.decision":
                        "allow",

                    "hitl.source":
                        "automatic",
                },
            ):

                pass

            print(
                f"[HITL] Automatically allowing "
                f"low-risk tool: {tool_name}"
            )

            return {
                "permissionDecision":
                    "allow",

                "permissionDecisionReason":
                    "Low-risk read-only operation.",
            }

        # ------------------------------------------------------
        # HUMAN APPROVAL
        # ------------------------------------------------------

        self.approval_required = True

        self.pending_tool = tool_name

        self.pending_arguments = tool_args

        self.approval_result = None

        self.approval_event = (
            asyncio.Event()
        )

        print("=" * 60)

        print(
            "HUMAN-IN-THE-LOOP APPROVAL REQUIRED"
        )

        print("=" * 60)

        print(
            f"Tool: {tool_name}"
        )

        print(
            f"Risk: {risk_level}"
        )

        print(
            f"Arguments: {tool_args}"
        )

        print("=" * 60)

        with optional_span(
            "copilot.tool.approval",
            {
                "tool.name":
                    tool_name,

                "tool.risk":
                    risk_level,

                "hitl.source":
                    "human",
            },
        ) as span:

            await self.approval_event.wait()

            approved = (
                self.approval_result
            )

            if span:

                span.set_attribute(
                    "hitl.decision",
                    (
                        "allow"
                        if approved
                        else "deny"
                    ),
                )

        if approved:

            self.last_approval_decision = (
                "approved"
            )

            self.last_approved_tool = (
                tool_name
            )

            self.last_approved_arguments = (
                tool_args
            )

        else:

            self.last_approval_decision = (
                "rejected"
            )

            self.last_denied_operation = {
                "tool":
                    tool_name,

                "arguments":
                    tool_args,
            }

        self.approval_required = False
        self.pending_tool = None
        self.pending_arguments = None
        self.approval_result = None
        self.approval_event = None

        if approved:

            return {
                "permissionDecision":
                    "allow",

                "permissionDecisionReason":
                    "Explicitly approved by the user.",
            }

        return {
            "permissionDecision":
                "deny",

            "permissionDecisionReason":
                "Explicitly rejected by the user.",
        }

    # ==========================================================
    # POST TOOL
    # ==========================================================

    async def _post_tool_use(
        self,
        input_data,
        invocation,
    ):

        tool_name = input_data.get(
            "toolName",
            "unknown",
        )

        record_event_span(
            "copilot.tool.completed",
            {
                "tool.name":
                    tool_name,

                "tool.status":
                    "success",
            },
        )

    # ==========================================================
    # POST TOOL FAILURE
    # ==========================================================

    async def _post_tool_use_failure(
        self,
        input_data,
        invocation,
    ):

        tool_name = input_data.get(
            "toolName",
            "unknown",
        )

        record_event_span(
            "copilot.tool.completed",
            {
                "tool.name":
                    tool_name,

                "tool.status":
                    "failure",
            },
        )

    # ==========================================================
    # HITL
    # ==========================================================

    def get_pending_approval(self):

        if not self.approval_required:
            return None

        return {
            "tool":
                self.pending_tool,

            "arguments":
                self.pending_arguments,
        }

    def approve(self):

        if (
            not self.approval_required
            or self.approval_event is None
        ):

            return False

        self.approval_result = True

        self.loop.call_soon_threadsafe(
            self.approval_event.set
        )

        return True

    def reject(self):

        if (
            not self.approval_required
            or self.approval_event is None
        ):

            return False

        self.approval_result = False

        self.loop.call_soon_threadsafe(
            self.approval_event.set
        )

        return True

    # ==========================================================
    # ASK
    # ==========================================================

    def ask(
        self,
        prompt: str,
    ):

        if self.loop is None:

            raise RuntimeError(
                "Copilot event loop is not running."
            )

        if self.session is None:

            raise RuntimeError(
                "Copilot session is not initialized."
            )

        self.last_approval_decision = None
        self.last_approved_tool = None
        self.last_approved_arguments = None
        self.last_denied_operation = None

        future = (
            asyncio.run_coroutine_threadsafe(
                self._async_ask(prompt),
                self.loop,
            )
        )

        return future.result()

    async def _async_ask(
        self,
        prompt,
    ):

        with optional_span(
            "copilot.agent.turn",
            {
                "openinference.span.kind":
                    "AGENT",

                "copilot.prompt":
                    prompt[:1000],
            },
        ):

            try:

                response = (
                    await self.session.send_and_wait(
                        prompt
                    )
                )

                if (
                    self.last_approval_decision
                    == "rejected"
                ):

                    return (
                        "❌ **Operation declined**\n\n"
                        "The requested operation was "
                        "rejected and was **not performed**."
                    )

                if (
                    self.last_approval_decision
                    == "approved"
                ):

                    return (
                        "✅ **Operation approved**\n\n"
                        f"{response.data.content}"
                    )

                return response.data.content

            finally:

                flush_traces()

    # ==========================================================
    # BACKGROUND
    # ==========================================================

    def ask_background(
        self,
        prompt: str,
    ):

        if self.agent_running:
            return False

        self.agent_result = None
        self.agent_error = None
        self.agent_running = True

        def worker():

            try:

                self.agent_result = (
                    self.ask(prompt)
                )

            except Exception as e:

                self.agent_error = str(e)

            finally:

                self.agent_running = False

        thread = threading.Thread(
            target=worker,
            daemon=True,
        )

        thread.start()

        return True

    # ==========================================================
    # STATE
    # ==========================================================

    def get_agent_state(self):

        return {
            "running":
                self.agent_running,

            "result":
                self.agent_result,

            "error":
                self.agent_error,
        }

    def clear_agent_result(self):

        self.agent_result = None
        self.agent_error = None

    # ==========================================================
    # STOP
    # ==========================================================

    def stop(self):

        if self.loop is None:
            return

        try:

            future = (
                asyncio.run_coroutine_threadsafe(
                    self._async_stop(),
                    self.loop,
                )
            )

            future.result(
                timeout=10
            )

        except Exception:
            pass

        try:

            self.loop.call_soon_threadsafe(
                self.loop.stop
            )

        except Exception:
            pass

        self.client = None
        self.session = None
        self.repository_path = None

        self.loop = None
        self.loop_thread = None

        self.agent_running = False

    async def _async_stop(self):

        if self.client is not None:

            await self.client.stop()

        flush_traces()