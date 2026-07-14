import os

from dotenv import load_dotenv

# from langchain_core.tools import tool
from newsapi import NewsApiClient

from common.exceptions import NewsAPIError

load_dotenv()

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

# Init
newsapi = NewsApiClient(api_key=os.environ.get("NEWS_API_KEY"))


# /v2/top-headlines


###　ニュースを取得する関数
def get_top_headlines(
    query: str,
    sources: str = None,
    category: str = None,
    language: str = "en",
    country: str = None,
):
    print(
        f"Fetching top headlines with query: {query}, sources: {sources}, category: {category}, language: {language}, country: {country}"
    )

    try:
        top_headlines = newsapi.get_top_headlines(
            q=query,
            sources=sources,
            category=category,
            language=language,
            country=country,
        )

        if top_headlines.get("status") != "ok":
            raise NewsAPIError(top_headlines.get("message"))

        return top_headlines.get("articles")

    except NewsAPIError:
        raise

    except Exception as e:
        raise NewsAPIError(f"Error fetching top headlines: {str(e)}") from e


# /v2/everything
def get_everything(
    query: str,
    sources: str,
    domains: str,
    from_param: str,
    to: str,
    language: str,
    sort_by: str,
    page: int,
):
    return newsapi.get_everything(
        q=query,
        sources=sources,
        domains=domains,
        from_param=from_param,
        to=to,
        language=language,
        sort_by=sort_by,
        page=page,
    )


# /v2/top-headlines/sources
def get_sources(category: str, language: str, country: str):

    return newsapi.get_sources()
