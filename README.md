# ニュース要約 LINE 配信エージェント

指定したカテゴリのニュースを NewsAPI から取得し、GPT-4o で日本語200文字以内に要約して LINE に送信する LangGraph エージェントです。X（Twitter）への投稿ツールも備えています。

## 動作環境

- Python 3.11（`langchain` / `chromadb` の固定版に合わせています）
- Windows / macOS / Linux

## セットアップ

### 1. クローンと仮想環境の作成

```bash
git clone <このリポジトリのURL>
cd report_20260714
```

Windows (PowerShell):

```powershell
py -3.11 -m venv venv
venv\Scripts\Activate.ps1
```

macOS / Linux:

```bash
python3.11 -m venv venv
source venv/bin/activate
```

### 2. 依存パッケージのインストール

```bash
pip install -r requirements.txt
```

### 3. API キーの取得

このアプリは外部サービスのキーがないと動きません。以下を各サイトで取得してください。

| サービス | 用途 | 取得先 |
| --- | --- | --- |
| OpenAI | 要約を行う LLM (gpt-4o) | https://platform.openai.com/api-keys |
| NewsAPI | ニュース記事の取得 | https://newsapi.org/register |
| LINE Messaging API | 要約の送信先 | https://developers.line.biz/console/ |
| X (Twitter) API | ツイート投稿（任意） | https://developer.x.com/ |

### 4. `.env` の作成

リポジトリ直下に `.env` を作成し、取得したキーを設定します（`.env` は Git 管理外です）。

```dotenv
# OpenAI
OPENAI_API_KEY=sk-...

# News API
NEWS_API_KEY=...

# LINE
LINE_ACCESS_TOKEN=...
LINE_TO_USER_ID=...
LINE_TO_GROUP_ID=...

# X (Twitter) ※ツイート投稿を使う場合のみ
X_BEARER_TOKEN=...
X_CLIENT_ID=...
X_CLIENT_SECRET=...
```

`LINE_TO_GROUP_ID` は送信先グループの ID です。分からない場合は「LINE グループ ID の調べ方」を参照してください。

## 実行

```bash
python main.py
```

[main.py](main.py) は `run_agent("AI")` を呼び出し、AI 関連のニュースを取得 → 要約 → LINE 送信まで行います。カテゴリを変えたい場合は引数の文字列を書き換えてください。

## テスト

```bash
pytest
```

## LINE グループ ID の調べ方

送信先グループの ID は Webhook 経由でしか取得できません。

1. `python line/line_webhook.py` でポート 8000 の待受サーバーを起動します。
2. devtunnels や ngrok などで 8000 番を HTTPS で公開します。
3. LINE Developers コンソールの Webhook URL に公開 URL を設定します。
4. 対象グループで発言すると、ターミナルに `groupId` が表示されます。

## ディレクトリ構成

| パス | 内容 |
| --- | --- |
| [main.py](main.py) | エントリポイント |
| [agent/](agent/) | LangGraph の ReAct エージェント定義とシステムプロンプト |
| [news/](news/) | NewsAPI 呼び出しと記事の整形 |
| [line/](line/) | LINE 送信 API と Webhook 受信サーバー |
| [x/](x/) | X API 呼び出しと OAuth2 (PKCE) 認可フロー |
| [common/](common/) | 共通の型定義・例外・ユーティリティ |
| [tests/](tests/) | pytest のテストコード |

## 既知の注意点

### X（Twitter）投稿は追加の対応が必要です

ニュース取得と LINE 送信だけを使う場合は関係ありません。ツイート投稿を使う場合、クローン直後の状態では以下の1点で失敗します。

1. **`token.json` が存在しない** — [x_oauth.py:80](x/x_oauth/x_oauth.py#L80) は起動時に `token.json` を無条件で読み込みますが、このファイルは Git 管理外のため、クローン直後には存在せず `FileNotFoundError` になります。暫定的には、以下の内容で `token.json` をリポジトリ直下に作成するとブラウザ認可フローが走ります。

   ```json
   {
     "access_token": "",
     "refresh_token": "",
     "access_token_expires_in": 0
   }
   ```

### `fix_venv.bat` について

[fix_venv.bat](fix_venv.bat) は、既存の `venv` を別マシンに持ち込んだ際に `pyvenv.cfg` のパスを修復するための補助スクリプトです。クローンから始める場合は `venv` を新規作成するため、実行する必要はありません。
