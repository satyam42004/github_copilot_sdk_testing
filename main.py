import asyncio
import json
from contextlib import nullcontext

from copilot import CopilotClient, ToolSet
from copilot.session import PermissionHandler
from copilot.session_events import SessionEventType

from tools import list_files, read_file, search_code
from tools.repository import get_repository_path
from observability import (
    configure_tracing,
    get_tracer,
    is_tracing_enabled,
    optional_span,
    record_event_span,
)


# ============================================================
# USAGE TRACKER
# ============================================================

class UsageTracker:
    """
    Tracks Copilot model usage during a session.
    """

    def __init__(self):
        self.model = None

        self.input_tokens = 0
        self.output_tokens = 0
        self.cache_read_tokens = 0
        self.cache_write_tokens = 0
        self.reasoning_tokens = 0

        self.ai_credits = 0.0
        self.total_nano_aiu = 0.0

    def handle_event(self, event):
        """
        Handle Copilot usage events.
        """

        # ----------------------------------------------------
        # Per-model-call usage
        # ----------------------------------------------------

        if event.type == SessionEventType.ASSISTANT_USAGE:

            data = event.data

            self.model = data.model

            self.input_tokens += data.input_tokens or 0
            self.output_tokens += data.output_tokens or 0
            self.cache_read_tokens += data.cache_read_tokens or 0
            self.cache_write_tokens += data.cache_write_tokens or 0
            self.reasoning_tokens += data.reasoning_tokens or 0

            if data.cost is not None:
                self.ai_credits += data.cost

            record_event_span(
                "copilot.usage",
                {
                    "gen_ai.request.model": data.model or "unknown",
                    "gen_ai.usage.input_tokens": data.input_tokens or 0,
                    "gen_ai.usage.output_tokens": data.output_tokens or 0,
                    "copilot.usage.cache_read_tokens": (
                        data.cache_read_tokens or 0
                    ),
                    "copilot.usage.cache_write_tokens": (
                        data.cache_write_tokens or 0
                    ),
                    "copilot.usage.reasoning_tokens": (
                        data.reasoning_tokens or 0
                    ),
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

        # ----------------------------------------------------
        # Session-level usage checkpoint
        # ----------------------------------------------------

        elif event.type == SessionEventType.SESSION_USAGE_CHECKPOINT:

            data = event.data

            self.total_nano_aiu = data.total_nano_aiu

            # SDK 1.0.11 exposes this field in the generated
            # usage data object.
            if data._total_premium_requests is not None:
                self.ai_credits = data._total_premium_requests

    def print_summary(self):
        """
        Print final usage after the session completes.
        """

        total_tokens = (
            self.input_tokens
            + self.output_tokens
        )

        print("\n")
        print("=" * 60)
        print("COPILOT SESSION USAGE SUMMARY")
        print("=" * 60)

        print(f"Model:              {self.model}")
        print(f"Input tokens:       {self.input_tokens}")
        print(f"Output tokens:      {self.output_tokens}")
        print(f"Total tokens:       {total_tokens}")
        print(f"Cache read tokens:  {self.cache_read_tokens}")
        print(f"Cache write tokens: {self.cache_write_tokens}")
        print(f"Reasoning tokens:   {self.reasoning_tokens}")
        print(f"AI credits:         {self.ai_credits}")
        print(f"Total nano AIU:     {self.total_nano_aiu}")

        print("=" * 60)


# ============================================================
# HUMAN-IN-THE-LOOP
# ============================================================

async def pre_tool_use_handler(input_data, invocation):
    """
    Risk-based Human-in-the-Loop policy.
    """

    tool_name = input_data["toolName"]
    tool_args = input_data["toolArgs"]

    # --------------------------------------------------
    # LOW RISK: Custom read-only repository tools
    # --------------------------------------------------

    read_only_tools = {
        "list_files",
        "read_file",
        "search_code",
    }

    if tool_name in read_only_tools:

        record_event_span(
            "hitl.tool_approval",
            {
                "tool.name": tool_name,
                "hitl.risk_level": "LOW",
                "hitl.decision": "allow",
                "hitl.decision_source": "automatic",
            },
        )

        print(
            f"\n[OK] Automatically allowing read-only tool: "
            f"{tool_name}"
        )

        return {
            "permissionDecision": "allow",
            "permissionDecisionReason": (
                "Read-only repository operation"
            ),
        }

    # --------------------------------------------------
    # Default risk
    # --------------------------------------------------

    risk_level = "MEDIUM"
    command = ""

    # --------------------------------------------------
    # POWERSHELL RISK ANALYSIS
    # --------------------------------------------------

    if tool_name == "powershell":

        if isinstance(tool_args, str):

            try:

                parsed_args = json.loads(tool_args)

                command = str(
                    parsed_args.get("command", "")
                ).strip()

            except json.JSONDecodeError:

                command = tool_args

        elif isinstance(tool_args, dict):

            command = str(
                tool_args.get("command", "")
            ).strip()

        command_lower = command.lower()

        # ----------------------------------------------
        # HIGH RISK commands
        # ----------------------------------------------

        high_risk_patterns = [
            "remove-item",
            "remove-",
            "del ",
            "erase ",
            "rmdir",
            "rd ",
            "format-volume",
            "format-disk",
            "clear-content",
            "set-content",
            "add-content",
            "out-file",
            "move-item",
            "rename-item",
            "git push",
            "git reset --hard",
            "git clean",
            "git rebase",
        ]

        if any(
            pattern in command_lower
            for pattern in high_risk_patterns
        ):

            risk_level = "HIGH"

        # ----------------------------------------------
        # LOW RISK commands
        # ----------------------------------------------

        elif any(
            command_lower.startswith(cmd)
            for cmd in [
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
            ]
        ):

            risk_level = "LOW"

        # ----------------------------------------------
        # Automatically allow LOW risk
        # ----------------------------------------------

        if risk_level == "LOW":

            record_event_span(
                "hitl.tool_approval",
                {
                    "tool.name": tool_name,
                    "hitl.risk_level": risk_level,
                    "hitl.decision": "allow",
                    "hitl.decision_source": "automatic",
                },
            )

            print(
                f"\n[OK] Automatically allowing low-risk "
                f"PowerShell command: {command}"
            )

            return {
                "permissionDecision": "allow",
                "permissionDecisionReason": (
                    "Known low-risk read-only "
                    "PowerShell command"
                ),
            }

    # --------------------------------------------------
    # HUMAN-IN-THE-LOOP
    # --------------------------------------------------

    print("\n" + "=" * 60)
    print("HUMAN-IN-THE-LOOP APPROVAL")
    print("=" * 60)

    print(f"Tool: {tool_name}")
    print(f"Risk: {risk_level}")

    if tool_name == "powershell":
        print(f"Command: {command}")
    else:
        print(f"Arguments: {tool_args}")

    print("\nThis operation requires human approval.")
    print("1. Approve")
    print("2. Reject")

    with optional_span(
        "hitl.tool_approval",
        attributes={
            "tool.name": tool_name,
            "hitl.risk_level": risk_level,
            "hitl.decision_source": "human",
        },
    ) as span:
        choice = input("\nEnter choice: ").strip()

        if choice == "1":

            if span:
                span.set_attribute("hitl.decision", "allow")
            print("[OK] Tool approved")

            return {
                "permissionDecision": "allow",
                "permissionDecisionReason": (
                    f"Human approved "
                    f"{risk_level.lower()} risk operation"
                ),
            }

        span.set_attribute("hitl.decision", "deny")
        print("[REJECT] Tool rejected")

        return {
            "permissionDecision": "deny",
            "permissionDecisionReason": (
                "Human rejected the operation"
            ),
        }


# ============================================================
# MAIN
# ============================================================

async def main():

    print("Starting Copilot SDK...")

    # --------------------------------------------------------
    # Create usage tracker
    # --------------------------------------------------------

    usage_tracker = UsageTracker()

    # Phoenix tracing is optional and can be enabled via environment variable
    # For now, keeping it disabled due to CLI compatibility issues
    tracer_provider = None
    
    print("\n[INFO] OpenTelemetry tracing is disabled by default")
    print("[INFO] To enable Phoenix tracing, set PHOENIX_ENABLED=true")
    print("[INFO] (Note: Currently causes issues with Copilot SDK CLI v1.0.79)\n")

    # --------------------------------------------------------
    # Start Copilot
    # --------------------------------------------------------

    # Create client WITHOUT telemetry configuration
    # The CLI v1.0.79 has compatibility issues with OpenTelemetry
    client = CopilotClient()

    with optional_span("copilot.client.start"):
        await client.start()

    print("Copilot started.")

    # --------------------------------------------------------
    # CREATE COPILOT SESSION
    # --------------------------------------------------------

    with optional_span("copilot.session.create"):
        session = await client.create_session(

        # ----------------------------------------------------
        # Repository
        # ----------------------------------------------------

        working_directory=str(
            get_repository_path()
        ),

        # ----------------------------------------------------
        # Permission handler
        # ----------------------------------------------------

        on_permission_request=(
            PermissionHandler.approve_all
        ),

        # ----------------------------------------------------
        # Human-in-the-loop hook
        # ----------------------------------------------------

        hooks={
            "on_pre_tool_use": (
                pre_tool_use_handler
            ),
        },

        # ----------------------------------------------------
        # Usage event handler
        # ----------------------------------------------------

        on_event=usage_tracker.handle_event,

        # ----------------------------------------------------
        # Prevent built-in create tool
        # ----------------------------------------------------

        excluded_tools=(
            ToolSet()
            .add_builtin("create")
        ),

        # ----------------------------------------------------
        # AGENT PERSONA / SYSTEM MESSAGE
        # ----------------------------------------------------

        system_message={
            "mode": "append",
            "content": """
You are a Senior Software Engineering Repository Agent.

PERSONA:
- Act like an experienced software engineer working on an existing codebase.
- Be precise, methodical, and conservative with changes.
- Understand the repository before making conclusions or changes.
- Base your answers on actual repository information returned by tools.
- Never invent files, technologies, architecture, or implementation details.

REPOSITORY BEHAVIOR:
- Inspect the repository structure before analyzing individual files.
- Use search tools when looking for specific code, symbols, or functionality.
- Read relevant files before explaining how they work.
- Prefer existing project conventions over introducing unnecessary patterns.
- Keep changes minimal and focused when modifications are requested.

SAFETY:
- Treat read-only operations as low risk.
- Treat modifications, deletions, commits, pushes, and other potentially irreversible operations as high risk.
- High-risk operations must go through the Human-in-the-Loop approval mechanism.
- Never expose, print, or reveal authentication credentials, tokens, or secrets.

HUMAN-IN-THE-LOOP:
- Do not bypass Human-in-the-Loop approval.
- If an operation requires approval, wait for the user's decision.
- Do not retry a rejected operation using another tool.
- Clearly explain what action you intend to perform.
- Prefer read-only operations whenever they are sufficient.

COMMUNICATION:
- Clearly explain what you found.
- Distinguish facts from assumptions.
- If information cannot be determined from the repository, explicitly say so.
- After making changes, verify the result when possible.
""",
        },

        # ----------------------------------------------------
        # MODEL
        # ----------------------------------------------------

        model="auto",

        # ----------------------------------------------------
        # CUSTOM REPOSITORY TOOLS
        # ----------------------------------------------------

        tools=[
            list_files,
            read_file,
            search_code,
        ],
        )

    print("Repository tools configured.")

    # --------------------------------------------------------
    # TEST REQUEST
    # --------------------------------------------------------

    with optional_span(
        "copilot.agent.turn",
        attributes={
            "openinference.span.kind": "AGENT",
        },
    ):
        response = await session.send_and_wait(
            """
Create a file named hitl_policy_test.txt in the repository
with the following content:

HITL policy test.

This is a test of the Human-in-the-Loop mechanism.
"""
        )

    # --------------------------------------------------------
    # ASSISTANT RESPONSE
    # --------------------------------------------------------

    print("\nAssistant:")
    print(response.data.content)

    # --------------------------------------------------------
    # FINAL SESSION USAGE
    # --------------------------------------------------------

    usage_tracker.print_summary()

    # --------------------------------------------------------
    # STOP COPILOT
    # --------------------------------------------------------

    with optional_span("copilot.client.stop"):
        await client.stop()

    if tracer_provider:
        tracer_provider.force_flush()

    print("\nCopilot stopped.")


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    asyncio.run(main())
