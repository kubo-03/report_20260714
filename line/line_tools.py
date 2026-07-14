import asyncio

from langchain_core.tools import tool

from common.exceptions import LineAPIError
from line import line_api


@tool
async def send_line_tool(
    text: str,
):
    """
    ### 概要
    ラインを送るためのツール

    ### 引数
    - text: メッセージ

    ### 返り値
    - なし
    """

    try:
        await asyncio.to_thread(
            line_api.send_line,
            text,
        )
    except Exception as e:
        raise LineAPIError(f"LineAPI呼び出しに失敗しました:{str(e)}")
