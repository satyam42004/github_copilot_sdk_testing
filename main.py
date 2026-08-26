import asyncio

from copilot import CopilotClient, ToolSet
from copilot.session import PermissionHandler

from tools import list_files, read_file, search_code
from tools.repository import get_repository_path

async def pre_tool_use_handler(input_data, invocation):
    """
    Human-in-the-loop approval based on tool risk.
    """

    tool_name = input_data["toolName"]
    tool_args = input_data["toolArgs"]

    read_only_tools = {
        "list_files",
        "read_file",
        "search_code",
    }

    if tool_name in read_only_tools:
        print(f"\n✓ Automatically allowing read-only tool: {tool_name}")

        return {
            "permissionDecision": "allow",
            "permissionDecisionReason": "Read-only tool",
        }

    print("\n" + "=" * 60)
    print("HUMAN-IN-THE-LOOP APPROVAL")
    print("=" * 60)

    print(f"Tool: {tool_name}")
    print(f"Arguments: {tool_args}")

    print("\nThis tool requires human approval.")
    print("1. Approve")
    print("2. Reject")

    choice = input("\nEnter choice: ").strip()

    if choice == "1":
        print("✓ Tool approved")

        return {
            "permissionDecision": "allow",
            "permissionDecisionReason": "Approved by user",
        }

    print("✗ Tool rejected")

    return {
        "permissionDecision": "deny",
        "permissionDecisionReason": "Rejected by user",
    }

async def main():
    print("Starting Copilot SDK...")

    client = CopilotClient()

    await client.start()

    print("Copilot started.")

    session = await client.create_session(
    working_directory=str(get_repository_path()),

    on_permission_request=PermissionHandler.approve_all,

    hooks={
        "on_pre_tool_use": pre_tool_use_handler,
    },

    excluded_tools=ToolSet().add_builtin("create"),

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

COMMUNICATION:
- Clearly explain what you found.
- Distinguish facts from assumptions.
- If information cannot be determined from the repository, explicitly say so.
- After making changes, verify the result when possible.
"""
    },

    model="auto",

    tools=[
        list_files,
        read_file,
        search_code,
    ],
)

    print("Repository tools configured.")

    response = await session.send_and_wait(
        """
Create a file named hitl_test.txt in the repository with the content:

Human-in-the-loop test successful.
"""
    )

    print("\nAssistant:")
    print(response.data.content)

    await client.stop()

    print("\nCopilot stopped.")


if __name__ == "__main__":
    asyncio.run(main())