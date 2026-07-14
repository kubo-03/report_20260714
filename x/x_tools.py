from langchain_core.tools import tool

from common.exceptions import XAPIError
from x import x_api


@tool
async def create_tweet(
    text: str,
):
    """
    ### 概要
    ツイートを作成する関数です。

    ### 引数
    - text: ツイートの内容

    ### 返り値
    - 作成されたツイートの情報
    """

    try:
        result = await x_api.get_create_post(text=text)
    except XAPIError:
        raise

    return result
