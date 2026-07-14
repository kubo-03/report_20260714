class AppError(Exception):
    """このアプリケーション共通の基底例外"""


class NewsAPIError(AppError):
    """NewsAPI呼び出しに失敗した場合の例外"""


class XAPIError(AppError):
    """XAPI呼び出しに失敗した場合の例外"""


class AuthenticationError(AppError):
    """認証・認可に失敗した場合の例外"""


class LineAPIError(AppError):
    """ラインAPI呼び出しに失敗した場合の例外"""
