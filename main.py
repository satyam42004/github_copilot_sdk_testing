import asyncio
import json

from copilot import CopilotClient, ToolSet
from copilot.session import PermissionHandler

from tools import list_files, read_file, search_code
from tools.repository import get_repository_path


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
        print(
            f"\n✓ Automatically allowing read-only tool: "
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

        # Copilot SDK may provide arguments as JSON string
        if isinstance(tool_args, str):
            try:
                parsed_args = json.loads(tool_args)

                command = str(
                    parsed_args.get("command", "")
                ).strip()

            except json.JSONDecodeError:
                command = tool_args

        # Handle dictionary arguments
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
            print(
                f"\n✓ Automatically allowing low-risk "
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

    choice = input("\nEnter choice: ").strip()

    if choice == "1":

        print("✓ Tool approved")

        return {
            "permissionDecision": "allow",
            "permissionDecisionReason": (
                f"Human approved "
                f"{risk_level.lower()} risk operation"
            ),
        }

    print("✗ Tool rejected")

    return {
        "permissionDecision": "deny",
        "permissionDecisionReason": (
            "Human rejected the operation"
        ),
    }


async def main():

    print("Starting Copilot SDK...")

    client = CopilotClient()

    await client.start()

    print("Copilot started.")

    # --------------------------------------------------
    # CREATE COPILOT SESSION
    # --------------------------------------------------

    session = await client.create_session(

        # Use the configured repository as the
        # Copilot working directory
        working_directory=str(
            get_repository_path()
        ),

        # SDK permission handler
        on_permission_request=(
            PermissionHandler.approve_all
        ),

        # Human-in-the-loop hook
        hooks={
            "on_pre_tool_use": (
                pre_tool_use_handler
            ),
        },

        # Prevent the built-in create tool from
        # directly creating files.
        excluded_tools=(
            ToolSet()
            .add_builtin("create")
        ),

        # --------------------------------------------------
        # AGENT PERSONA
        # --------------------------------------------------

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

        model="auto",

        # --------------------------------------------------
        # CUSTOM REPOSITORY TOOLS
        # --------------------------------------------------

        tools=[
            list_files,
            read_file,
            search_code,
        ],
    )

    print("Repository tools configured.")

    # --------------------------------------------------
    # TEST REQUEST
    # --------------------------------------------------

    response = await session.send_and_wait(
       """
Create a file named hitl_policy_test.txt in the repository
with the following content:

HITL policy test.

This is a test of the Human-in-the-Loop mechanism.
"""
    )

    print("\nAssistant:")
    print(response.data.content)

    await client.stop()

    print("\nCopilot stopped.")


if __name__ == "__main__":
    asyncio.run(main())