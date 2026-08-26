import sqlite3
from pathlib import Path

from fastmcp import FastMCP


DB_PATH = Path(__file__).resolve().parent.parent / "data" / "tickets.db"

mcp = FastMCP(
    "Enterprise Ticket System"
)


def get_connection():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(DB_PATH)

    connection.row_factory = sqlite3.Row

    return connection


def initialize_database():
    connection = get_connection()

    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS tickets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            priority TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'open'
        )
        """
    )

    connection.commit()
    connection.close()


@mcp.tool
def create_ticket(
    title: str,
    description: str,
    priority: str = "medium",
) -> dict:
    """
    Create a new enterprise support ticket.
    """

    allowed_priorities = {
        "low",
        "medium",
        "high",
        "critical",
    }

    priority = priority.lower()

    if priority not in allowed_priorities:
        return {
            "success": False,
            "error": (
                "Invalid priority. Use: "
                "low, medium, high, or critical."
            ),
        }

    connection = get_connection()

    cursor = connection.execute(
        """
        INSERT INTO tickets (
            title,
            description,
            priority
        )
        VALUES (?, ?, ?)
        """,
        (
            title,
            description,
            priority,
        ),
    )

    connection.commit()

    ticket_id = cursor.lastrowid

    connection.close()

    return {
        "success": True,
        "ticket_id": f"TKT-{ticket_id:04d}",
        "title": title,
        "priority": priority,
        "status": "open",
    }


@mcp.tool
def get_ticket(ticket_id: str) -> dict:
    """
    Retrieve an enterprise support ticket by ID.
    """

    if not ticket_id.startswith("TKT-"):
        return {
            "success": False,
            "error": "Invalid ticket ID format.",
        }

    try:
        numeric_id = int(ticket_id.replace("TKT-", ""))
    except ValueError:
        return {
            "success": False,
            "error": "Invalid ticket ID.",
        }

    connection = get_connection()

    ticket = connection.execute(
        """
        SELECT
            id,
            title,
            description,
            priority,
            status
        FROM tickets
        WHERE id = ?
        """,
        (numeric_id,),
    ).fetchone()

    connection.close()

    if ticket is None:
        return {
            "success": False,
            "error": "Ticket not found.",
        }

    return {
        "success": True,
        "ticket_id": f"TKT-{ticket['id']:04d}",
        "title": ticket["title"],
        "description": ticket["description"],
        "priority": ticket["priority"],
        "status": ticket["status"],
    }


@mcp.tool
def search_tickets(
    query: str,
) -> list[dict]:
    """
    Search enterprise support tickets by title or description.
    """

    connection = get_connection()

    pattern = f"%{query}%"

    tickets = connection.execute(
        """
        SELECT
            id,
            title,
            description,
            priority,
            status
        FROM tickets
        WHERE title LIKE ?
           OR description LIKE ?
        ORDER BY id DESC
        """,
        (
            pattern,
            pattern,
        ),
    ).fetchall()

    connection.close()

    return [
        {
            "ticket_id": f"TKT-{ticket['id']:04d}",
            "title": ticket["title"],
            "description": ticket["description"],
            "priority": ticket["priority"],
            "status": ticket["status"],
        }
        for ticket in tickets
    ]


if __name__ == "__main__":
    initialize_database()

    mcp.run()