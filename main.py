import asyncio

from dotenv import load_dotenv

from agent import run_agent

load_dotenv()


async def main():

    # ツールを使って計算する例
    # calculate_tools_response = calculate_tools.run_agent(
    #     "10 と 20 を掛け算してください。"
    # )
    # print(calculate_tools_response)

    # ニュース記事を取得する例

    # print(result)
    try:
        news_summary = await run_agent.run_agent("AI")
        print(news_summary)

    except Exception as e:
        print("run_agent:", e)


if __name__ == "__main__":
    asyncio.run(main())
