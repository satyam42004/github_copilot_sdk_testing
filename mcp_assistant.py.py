import asyncio

from copilot import CopilotClient


async def main():
    print("Starting Copilot SDK...")

    client = CopilotClient()

    await client.start()

    print("Copilot started.")

    session = await client.create_session(
        model="auto",
        mcp_servers={
            "github": {
                "type": "http",
                "url": "https://api.githubcopilot.com/mcp/",
                "headers": {
                    "Authorization": "Bearer ${GITHUB_TOKEN}"
                },
                "tools": ["*"],
            }
        },
    )

    print("GitHub MCP configured.")

    

    response = await session.send_and_wait(
    "Search the repository satyam42004/enterprise-knowledge-assistant for "
    "code. Read requirements.txt and on based on that tell me what this project possibly does?."
)


    print("\nAssistant:")
    print(response.data.content)

    await client.stop()

    print("Copilot stopped.")


if __name__ == "__main__":
    asyncio.run(main())