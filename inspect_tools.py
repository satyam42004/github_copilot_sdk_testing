import asyncio

from copilot import CopilotClient


async def main():
    client = CopilotClient(
        use_logged_in_user=True
    )

    await client.start()

    session = await client.create_session(
        model="gpt-5-mini"
    )

    print("SESSION CREATED")
    print()
    print("Session attributes containing 'tool':")

    for name in dir(session):
        if "tool" in name.lower():
            print(name)

    await client.stop()


if __name__ == "__main__":
    asyncio.run(main())