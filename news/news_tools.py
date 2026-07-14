import asyncio

from langchain_core.tools import tool

from common.exceptions import NewsAPIError
from news import news_post
from news.news_processor import process_articles


@tool
async def get_top_headlines(
    query: str,
    sources: str = None,
    category: str = None,
    language: str = "en",
    country: str = None,
):
    """
    ### 概要
    ニュース記事のトップヘッドラインを取得する関数です。

    ### 引数
    - query: 検索クエリ
    - sources: ニュースソースのID（カンマ区切りで複数指定可能）
    - category: ニュースのカテゴリ（business, entertainment, general, health, science, sports, technology）
    - language: 言語（デフォルトは"en"）
    - country: 国（デフォルトはNone）

    ### 返り値
    - ニュース記事のトップヘッドラインのリスト
    """

    try:
        raw_articles = await asyncio.to_thread(
            news_post.get_top_headlines,
            query,
            sources=sources,
            category=category,
            language=language,
            country=country,
        )
    except NewsAPIError:
        raise

    try:
        articles = process_articles(raw_articles)
    except Exception as e:
        raise NewsAPIError(f"Error processing articles: {e}") from e

    print(f"Processed {len(articles)} articles.")
    for article in articles:
        print(f"Title: {article['title']}, Description: {article['description']}")

    return articles
