from typing import TypedDict


class Article(TypedDict):
    title: str | None
    description: str | None
    url: str | None
    published_at: str | None
