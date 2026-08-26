import asyncio

from copilot import CopilotClient


async def main():
    print("Starting SDK...")

    client = CopilotClient(
        use_logged_in_user=True,
    )

    await client.start()

    print("Client started.")

    auth = await client.get_auth_status()

    print("\nAuthentication")
    print("----------------")
    print("Authenticated:", auth.isAuthenticated)
    print("Login:", auth.login)

    models = await client.list_models()

    print("\nAvailable models:")
    for model in models:
        print(f"- {model.id}")

    session = await client.create_session(
        model="auto",
    )

    print("\nSession created.")

    response = await session.send_and_wait(
        "Say hello and tell me what model you are using."
    )

    print("\nAssistant:")
    print(response.data.content)

    await client.stop()

    print("\nDone.")


if __name__ == "__main__":
    asyncio.run(main())