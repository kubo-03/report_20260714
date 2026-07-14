import asyncio
import os

import requests
from dotenv import load_dotenv

# from langchain_core.tools import tool


load_dotenv()

ACCESS_TOKEN = os.environ.get("LINE_ACCESS_TOKEN")
TO_USER_ID = os.environ.get("LINE_TO_USER_ID")
TO_GROUP_ID = os.environ.get("LINE_TO_GROUP_ID")


def send_line(text: str):
    resp = requests.post(
        "https://api.line.me/v2/bot/message/push",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {ACCESS_TOKEN}",
        },
        json={
            "to": TO_GROUP_ID,
            "messages": [{"type": "text", "text": text}],
        },
    )

    print("status:", resp.status_code)
    print("body:", resp.text)


if __name__ == "__main__":
    asyncio.run(send_line("これは自作アプリから送ったメッセージです"))
