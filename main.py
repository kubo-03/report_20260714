import asyncio

from dotenv import load_dotenv

from agent import run_agent

load_dotenv()


async def main():

    try:
        news_summary = await run_agent.run_agent("AI")
        print(news_summary)

    except Exception as e:
        print(e)


if __name__ == "__main__":
    asyncio.run(main())
