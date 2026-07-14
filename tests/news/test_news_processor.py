from news.news_processor import process_articles


# process_articlesのテスト
def test_process_articles():
    raw_articles = [
        {
            "title": "テスト記事1",
            "description": "説明1",
            "url": "https://example.com/article1",
            "publishedAt": "2023-01-01T00:00:00Z",
        },
        {
            "title": "テスト記事2",
            "description": "説明2",
            "url": "https://example.com/article2",
            "publishedAt": "2023-01-02T00:00:00Z",
        },
    ]

    processed_articles = process_articles(raw_articles)

    assert len(processed_articles) == 2
    assert processed_articles[0]["title"] == "テスト記事1"
    assert processed_articles[0]["description"] == "説明1"
    assert processed_articles[0]["url"] == "https://example.com/article1"
    assert processed_articles[0]["published_at"] == "2023-01-01T00:00:00Z"


# 記事に一部のキーが欠けている場合、エラーにならずNoneで埋まることのテスト
def test_process_articles_with_missing_keys():
    raw_articles = [{"title": "テスト記事"}]

    processed_articles = process_articles(raw_articles)

    assert processed_articles[0]["title"] == "テスト記事"
    assert processed_articles[0]["description"] is None
    assert processed_articles[0]["url"] is None
    assert processed_articles[0]["published_at"] is None


# 記事のキーは存在するが値がNoneの場合、そのままNoneで返ることのテスト
def test_process_articles_with_none_values():
    raw_articles = [
        {
            "title": "テスト記事1",
            "description": None,
            "url": None,
            "publishedAt": None,
        }
    ]

    processed_articles = process_articles(raw_articles)

    assert processed_articles[0]["title"] == "テスト記事1"
    assert processed_articles[0]["description"] is None
    assert processed_articles[0]["url"] is None
    assert processed_articles[0]["published_at"] is None


# 空リストを渡した場合は空リストが返ることのテスト
def test_process_articles_with_empty_list():
    assert process_articles([]) == []
