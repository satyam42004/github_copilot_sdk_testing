import sys
from contextlib import asynccontextmanager
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


SERVER_PATH = (
    Path(__file__).resolve().parent.parent
    / "mcp_server"
    / "ticket_server.py"
)


@asynccontextmanager
async def mcp_session():
    """
    Start the ticket MCP server and create an MCP client session.
    """

    server_parameters = StdioServerParameters(
        command=sys.executable,
        args=[str(SERVER_PATH)],
    )

    async with stdio_client(server_parameters) as (
        read_stream,
        write_stream,
    ):
        async with ClientSession(
            read_stream,
            write_stream,
        ) as session:

            await session.initialize()

            yield session


async def list_ticket_tools():
    """
    List tools exposed by the ticket MCP server.
    """

    async with mcp_session() as session:
        result = await session.list_tools()

        return [
            tool.name
            for tool in result.tools
        ]


async def create_ticket(
    title: str,
    description: str,
    priority: str = "medium",
):
    """
    Create a ticket through the MCP server.
    """

    async with mcp_session() as session:

        result = await session.call_tool(
            "create_ticket",
            {
                "title": title,
                "description": description,
                "priority": priority,
            },
        )

        return result


async def get_ticket(ticket_id: str):
    """
    Retrieve a ticket through the MCP server.
    """

    async with mcp_session() as session:

        result = await session.call_tool(
            "get_ticket",
            {
                "ticket_id": ticket_id,
            },
        )

        return result


async def search_tickets(query: str):
    """
    Search tickets through the MCP server.
    """

    async with mcp_session() as session:

        result = await session.call_tool(
            "search_tickets",
            {
                "query": query,
            },
        )

        return result