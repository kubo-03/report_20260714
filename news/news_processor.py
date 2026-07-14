from common.models import Article


def process_articles(articles: list[dict]) -> list[Article]:
    """取得した記事のリストを、必要な項目だけに整形して返す"""
    return [
        {
            "title": article.get("title"),
            "description": article.get("description"),
            "url": article.get("url"),
            "published_at": article.get("publishedAt"),
        }
        for article in articles
    ]
