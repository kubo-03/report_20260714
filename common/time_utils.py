import time

def is_expired(expires_at: float, buffer_seconds: int = 0) -> bool:
    """指定した時刻(UNIX秒)を過ぎていれば True を返す"""
    return time.time() >= (expires_at - buffer_seconds)