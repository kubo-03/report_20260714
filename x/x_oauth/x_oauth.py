import asyncio
import base64
import hashlib
import http.server
import json
import os
import secrets
import socketserver
import threading
import urllib.parse
import webbrowser
from datetime import datetime, timedelta

import requests

from common.exceptions import AuthenticationError
from common.time_utils import is_expired

# ========= 設定 =========
CLIENT_ID = os.environ.get("X_CLIENT_ID")
CLIENT_SECRET = os.environ.get("X_CLIENT_SECRET")
REDIRECT_URI = "http://127.0.0.1:8000/callback"
SCOPES = "tweet.read tweet.write users.read offline.access"
# offline.access を入れるとリフレッシュトークンも取れる
# ========================


AUTH_URL = "https://x.com/i/oauth2/authorize"
TOKEN_URL = "https://api.x.com/2/oauth2/token"


# --- PKCE: code_verifier と code_challenge を生成 ---
code_verifier = secrets.token_urlsafe(64)  # 43~128文字のランダム文字列
code_challenge = (
    base64.urlsafe_b64encode(hashlib.sha256(code_verifier.encode()).digest())
    .decode()
    .rstrip("=")
)

state = secrets.token_urlsafe(16)  # CSRF対策のためのランダム文字列

# --- 認可URLを組み立てる ---
params = {
    "response_type": "code",
    "client_id": CLIENT_ID,
    "redirect_uri": REDIRECT_URI,
    "scope": SCOPES,
    "state": state,
    "code_challenge": code_challenge,
    "code_challenge_method": "S256",
}
authorize_url = f"{AUTH_URL}?{urllib.parse.urlencode(params)}"

# --- コールバックを受け取る簡易HTTPサーバー ---
auth_code_holder = {}


class CallbackHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        query = urllib.parse.urlparse(self.path).query
        params = urllib.parse.parse_qs(query)
        if "code" in params:
            auth_code_holder["code"] = params["code"][0]
            auth_code_holder["state"] = params.get("state", [""])[0]
            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(
                "<h1>認可完了。ターミナルに戻ってください。</h1>".encode("utf-8")
            )
        else:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b"error")


class XTokenManager:
    def __init__(self):
        # 読み込み
        with open("token.json") as f:
            self.tokens = json.load(f)

    async def update_access_token(self, access_token, refresh_token, expires_in):

        expires_in_hours = expires_in / 60 / 60
        now = datetime.now()  # 現在日時
        new_limit_time = now + timedelta(hours=expires_in_hours)  # hours 時間加算

        print("有効期限：" + str(new_limit_time))
        tokens_result = {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "access_token_expires_in": new_limit_time.timestamp(),
        }
        # 更新
        with open("token.json", "w") as f:
            json.dump(tokens_result, f, indent=2)

    async def get_access_token(self):
        if not self.tokens["refresh_token"]:
            print("認可コード取得")
            return await self.authorize_via_browser()

        # アクセストークンがない場合または、アクセストークンが有効期限切れの場合
        if (
            is_expired(self.tokens["access_token_expires_in"])
            or not self.tokens["access_token"]
        ):
            print("アクセストークン有効期限切れ")

            # --- コードをアクセストークンに変換 ---
            # Confidential clinet なので Basic認証で client_id:client_secret を送る
            basic_auth = base64.b64encode(
                f"{CLIENT_ID}:{CLIENT_SECRET}".encode("utf-8")
            ).decode()

            headers = {
                "Authorization": f"Basic {basic_auth}",
                "Content-Type": "application/x-www-form-urlencoded",
            }

            data = {
                "grant_type": "refresh_token",
                "refresh_token": self.tokens["refresh_token"],
            }

            try:
                resp = await asyncio.to_thread(
                    requests.post, TOKEN_URL, headers=headers, data=data
                )
                print("\n=== トークンレスポンス ===")
                print(resp.status_code)
                print(resp.json())

                if resp.status_code != 200:
                    raise AuthenticationError(
                        f"認証失敗しました:ステータスコード{str(resp.status_code)}"
                    )

                new_tokens = resp.json()

                await self.update_access_token(
                    new_tokens["access_token"],
                    new_tokens["refresh_token"],
                    new_tokens["expires_in"],
                )
            except Exception as e:
                raise AuthenticationError(f"認証失敗しました:{str(e)}")

            return new_tokens["access_token"]

        else:
            print("有効期限切れでない")

            return self.tokens["access_token"]

    def run_server(self):
        with socketserver.TCPServer(("127.0.0.1", 8000), CallbackHandler) as httpd:
            httpd.handle_request()  # 1回だけ受け取る

    async def authorize_via_browser(self):

        try:
            server_thread = threading.Thread(target=self.run_server, daemon=True)
            server_thread.start()

            # --- ブラウザを開いて認可を促す ---
            print("ブラウザで認可を行ってください...")
            webbrowser.open(authorize_url)

            await asyncio.to_thread(server_thread.join)  # サーバーが終了するまで待つ

            # --- state検証 ---
            if auth_code_holder.get("state") != state:
                raise AuthenticationError(
                    "State mismatch. CSRF攻撃の可能性があります。"
                )

            auth_code = auth_code_holder["code"]
            print("\n認可コードを取得しました:", auth_code[:20], "...")

            # --- コードをアクセストークンに変換 ---
            # Confidential clinet なので Basic認証で client_id:client_secret を送る
            basic_auth = base64.b64encode(
                f"{CLIENT_ID}:{CLIENT_SECRET}".encode("utf-8")
            ).decode()

            headers = {
                "Authorization": f"Basic {basic_auth}",
                "Content-Type": "application/x-www-form-urlencoded",
            }

            data = {
                "grant_type": "authorization_code",
                "code": auth_code,
                "redirect_uri": REDIRECT_URI,
                "code_verifier": code_verifier,
            }

            resp = await asyncio.to_thread(
                requests.post, TOKEN_URL, headers=headers, data=data
            )

            if resp.status_code != 200:
                raise AuthenticationError(
                    f"認証失敗しました:ステータスコード{str(resp.status_code)}"
                )

            new_tokens = resp.json()

            await self.update_access_token(
                new_tokens["access_token"],
                new_tokens["refresh_token"],
                new_tokens["expires_in"],
            )

            return new_tokens["access_token"]

        except Exception as e:
            raise AuthenticationError(f"認証失敗しました:{str(e)}")
