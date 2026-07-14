import asyncio
import json
import time
from unittest.mock import AsyncMock, MagicMock, mock_open, patch

import pytest

from common.exceptions import AuthenticationError
from x.x_oauth import x_oauth
from x.x_oauth.x_oauth import CallbackHandler, XTokenManager


# 各テストの前後で auth_code_holder(モジュールグローバル)をクリーンな状態に保つ
@pytest.fixture(autouse=True)
def _reset_auth_code_holder():
    original = dict(x_oauth.auth_code_holder)
    x_oauth.auth_code_holder.clear()
    yield
    x_oauth.auth_code_holder.clear()
    x_oauth.auth_code_holder.update(original)


def _make_manager(tokens):
    # __init__ のファイル読み込みを経由せずにインスタンスを用意する
    manager = XTokenManager.__new__(XTokenManager)
    manager.tokens = tokens
    return manager


# __init__ が token.json を読み込んで self.tokens にセットすることのテスト
def test_init_loads_tokens_from_file():
    tokens = {
        "access_token": "a",
        "refresh_token": "r",
        "access_token_expires_in": 123.0,
    }
    with patch("builtins.open", mock_open(read_data=json.dumps(tokens))) as m:
        manager = XTokenManager()

    m.assert_called_once_with("token.json")
    assert manager.tokens == tokens


# アクセストークンが有効期限内の場合、リフレッシュせずそのまま返すことのテスト
def test_get_access_token_returns_existing_when_not_expired():
    manager = _make_manager(
        {
            "access_token": "a",
            "refresh_token": "r",
            "access_token_expires_in": time.time() + 3600,
        }
    )

    with patch.object(x_oauth, "is_expired", return_value=False), patch.object(
        x_oauth.requests, "post"
    ) as mock_post:
        result = asyncio.run(manager.get_access_token())

    assert result == "a"
    mock_post.assert_not_called()


# アクセストークンが期限切れの場合、リフレッシュトークンで再取得することのテスト
def test_get_access_token_refreshes_when_expired():
    manager = _make_manager(
        {
            "access_token": "old_a",
            "refresh_token": "r",
            "access_token_expires_in": time.time() - 10,
        }
    )
    manager.update_access_token = AsyncMock()

    fake_response = MagicMock(status_code=200)
    fake_response.json.return_value = {
        "access_token": "new_a",
        "refresh_token": "new_r",
        "expires_in": 7200,
    }

    with patch.object(x_oauth, "is_expired", return_value=True), patch.object(
        x_oauth.requests, "post", return_value=fake_response
    ) as mock_post:
        result = asyncio.run(manager.get_access_token())

    assert result == "new_a"
    manager.update_access_token.assert_awaited_once_with("new_a", "new_r", 7200)

    _, kwargs = mock_post.call_args
    assert kwargs["data"] == {"grant_type": "refresh_token", "refresh_token": "r"}
    assert kwargs["headers"]["Authorization"].startswith("Basic ")


# リフレッシュAPIが200以外を返した場合、ブラウザ認可フローにフォールバックすることのテスト
def test_get_access_token_falls_back_to_browser_on_refresh_failure():
    manager = _make_manager(
        {
            "access_token": "old_a",
            "refresh_token": "r",
            "access_token_expires_in": time.time() - 10,
        }
    )
    manager.authorize_via_browser = AsyncMock(return_value="browser_token")

    fake_response = MagicMock(status_code=400)
    fake_response.json.return_value = {"error": "invalid_grant"}

    with patch.object(x_oauth, "is_expired", return_value=True), patch.object(
        x_oauth.requests, "post", return_value=fake_response
    ):
        result = asyncio.run(manager.get_access_token())

    assert result == "browser_token"
    manager.authorize_via_browser.assert_awaited_once()


# refresh_token を保持していない場合、リフレッシュを試みずブラウザ認可フローに進むことのテスト
def test_get_access_token_without_refresh_token_calls_authorize_via_browser():
    manager = _make_manager(
        {"access_token": None, "refresh_token": "", "access_token_expires_in": 0}
    )
    manager.authorize_via_browser = AsyncMock(return_value="browser_token")

    with patch.object(x_oauth.requests, "post") as mock_post:
        result = asyncio.run(manager.get_access_token())

    assert result == "browser_token"
    mock_post.assert_not_called()


# update_access_token が新しいトークンと有効期限を token.json に書き込むことのテスト
def test_update_access_token_writes_expected_data():
    manager = _make_manager({})

    with patch("builtins.open", mock_open()) as m:
        asyncio.run(manager.update_access_token("acc", "ref", 3600))

    handle = m()
    written = "".join(call.args[0] for call in handle.write.call_args_list)
    data = json.loads(written)

    assert data["access_token"] == "acc"
    assert data["refresh_token"] == "ref"
    assert abs(data["access_token_expires_in"] - (time.time() + 3600)) < 5


# ブラウザ認可フローが正常に完了し、アクセストークンを取得できることのテスト
def test_authorize_via_browser_success():
    manager = _make_manager({})
    manager.update_access_token = AsyncMock()
    manager.run_server = MagicMock()  # 実ソケットで待受しないようにする

    x_oauth.auth_code_holder.update({"code": "auth_code_123", "state": x_oauth.state})

    fake_response = MagicMock(status_code=200)
    fake_response.json.return_value = {
        "access_token": "new_a",
        "refresh_token": "new_r",
        "expires_in": 7200,
    }

    with patch.object(x_oauth.webbrowser, "open") as mock_browser_open, patch.object(
        x_oauth.requests, "post", return_value=fake_response
    ) as mock_post:
        result = asyncio.run(manager.authorize_via_browser())

    assert result == "new_a"
    mock_browser_open.assert_called_once_with(x_oauth.authorize_url)
    manager.update_access_token.assert_awaited_once_with("new_a", "new_r", 7200)

    _, kwargs = mock_post.call_args
    assert kwargs["data"]["grant_type"] == "authorization_code"
    assert kwargs["data"]["code"] == "auth_code_123"
    assert kwargs["data"]["code_verifier"] == x_oauth.code_verifier


# state が一致しない場合(CSRF疑い)は AuthenticationError になることのテスト
def test_authorize_via_browser_state_mismatch_raises():
    manager = _make_manager({})
    manager.update_access_token = AsyncMock()
    manager.run_server = MagicMock()  # 実ソケットで待受しないようにする

    x_oauth.auth_code_holder.update({"code": "auth_code_123", "state": "different-state"})

    with patch.object(x_oauth.webbrowser, "open"):
        with pytest.raises(AuthenticationError, match="State mismatch"):
            asyncio.run(manager.authorize_via_browser())


# トークン交換APIが200以外を返した場合、AuthenticationError になることのテスト
def test_authorize_via_browser_token_exchange_failure_raises():
    manager = _make_manager({})
    manager.update_access_token = AsyncMock()
    manager.run_server = MagicMock()  # 実ソケットで待受しないようにする

    x_oauth.auth_code_holder.update({"code": "auth_code_123", "state": x_oauth.state})

    fake_response = MagicMock(status_code=400)

    with patch.object(x_oauth.webbrowser, "open"), patch.object(
        x_oauth.requests, "post", return_value=fake_response
    ):
        with pytest.raises(AuthenticationError, match="認証失敗しました"):
            asyncio.run(manager.authorize_via_browser())


# CallbackHandler.do_GET が code/state を受け取って auth_code_holder に格納することのテスト
def test_callback_handler_stores_code_and_state():
    handler = CallbackHandler.__new__(CallbackHandler)
    handler.path = "/callback?code=abc123&state=xyz"
    handler.send_response = MagicMock()
    handler.send_header = MagicMock()
    handler.end_headers = MagicMock()
    handler.wfile = MagicMock()

    handler.do_GET()

    assert x_oauth.auth_code_holder["code"] == "abc123"
    assert x_oauth.auth_code_holder["state"] == "xyz"
    handler.send_response.assert_called_once_with(200)


# CallbackHandler.do_GET が code を受け取れなかった場合、400を返すことのテスト
def test_callback_handler_missing_code_returns_400():
    handler = CallbackHandler.__new__(CallbackHandler)
    handler.path = "/callback?error=access_denied"
    handler.send_response = MagicMock()
    handler.send_header = MagicMock()
    handler.end_headers = MagicMock()
    handler.wfile = MagicMock()

    handler.do_GET()

    handler.send_response.assert_called_once_with(400)
    assert "code" not in x_oauth.auth_code_holder
