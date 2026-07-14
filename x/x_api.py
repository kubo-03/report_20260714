import asyncio
import os

import requests
from dotenv import load_dotenv
from xdk import Client

# from langchain_core.tools import tool


load_dotenv()

BEARER_TOKEN = os.environ.get("X_BEARER_TOKEN")

client = Client(bearer_token=BEARER_TOKEN)
url = "https://api.x.com/2/notes"


# tweetの取得
def get_recent_posts(query: str, max_results: int = 10):
    try:
        # Search for posts
        for page in client.posts.search_recent(query=query, max_results=max_results):
            print(page.data)
            if page.data and len(page.data) > 0:
                print(page.data[0])
                break

    except Exception as e:
        print(f"Error fetching recent posts: {e}")
        return None


# tweetの投稿
async def get_create_post(text: str):
    try:
        from x.x_oauth.x_oauth import XTokenManager

        manager = XTokenManager()

        result = await manager.get_access_token()

        url = "https://api.x.com/2/tweets"

        payload = {
            "made_with_ai": False,
            "text": text,
        }
        headers = {
            "Authorization": f"Bearer {result}",
            "Content-Type": "application/json",
        }

        response = await asyncio.to_thread(
            requests.post, url, json=payload, headers=headers
        )

        print(response.text)

    except Exception as e:
        print(f"Error fetching recent posts: {e}")
        return None


if __name__ == "__main__":
    asyncio.run(get_create_post())
