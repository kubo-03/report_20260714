from unittest.mock import patch

import pytest

from news import news_post
from common.exceptions import NewsAPIError


# トップヘッドラインを取得する関数のテスト
def test_get_top_headlines_returns_articles():
    fake_response = {
        "status": "ok",
        "articles": [{"title": "テスト記事", "description": "説明"}],
    }
    with patch.object(
        news_post.newsapi, "get_top_headlines", return_value=fake_response
    ):
        articles = news_post.get_top_headlines(query="テクノロジー")

    assert articles == fake_response["articles"]


# トップヘッドラインを取得する関数がエラーを返す場合のテスト
def test_get_top_headlines_raises_on_error_status():
    fake_response = {"status": "error", "message": "invalid API key"}
    with patch.object(
        news_post.newsapi, "get_top_headlines", return_value=fake_response
    ):
        with pytest.raises(NewsAPIError, match="invalid API key"):
            news_post.get_top_headlines(query="テクノロジー")


# トップヘッドラインを取得する関数が予期しないエラーをラップする場合のテスト
def test_get_top_headlines_wraps_unexpected_errors():
    with patch.object(
        news_post.newsapi, "get_top_headlines", side_effect=ValueError("boom")
    ):
        with pytest.raises(NewsAPIError):
            news_post.get_top_headlines(query="テクノロジー")


# sourcesとcategory/countryを同時指定した場合、newsapi側のValueErrorがNewsAPIErrorに変換されるテスト
def test_get_top_headlines_wraps_mutually_exclusive_params_error():
    with patch.object(
        news_post.newsapi,
        "get_top_headlines",
        side_effect=ValueError("cannot mix country/category param with sources param."),
    ):
        with pytest.raises(NewsAPIError, match="cannot mix"):
            news_post.get_top_headlines(
                query="テクノロジー", sources="bbc-news", category="technology"
            )
