import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


class WebhookHandler(BaseHTTPRequestHandler):
    # リバースプロキシ(devtunnels等)に合わせてHTTP/1.1で応答する
    protocol_version = "HTTP/1.1"

    def _reply(self, status=200, body=b"OK"):
        self.send_response(status)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))  # 長さを明示
        self.end_headers()
        self.wfile.write(body)

    # LINEの「検証」やヘルスチェックのGETにも200を返す
    def do_GET(self):
        self._reply(200, b"OK")

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length).decode("utf-8") if length else ""

        # 先に200を返す（LINEは素早い応答を要求する）
        self._reply(200, b"OK")

        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            print("JSONパース失敗:", raw)
            return

        for event in data.get("events", []):
            source = event.get("source", {})
            print("---- イベント ----")
            print("source.type :", source.get("type"))
            print("groupId     :", source.get("groupId"))   # グループのID
            print("roomId      :", source.get("roomId"))     # 複数人トークのID
            print("userId      :", source.get("userId"))
            print("full        :", json.dumps(source, ensure_ascii=False))

    def log_message(self, *args):
        pass


if __name__ == "__main__":
    server = ThreadingHTTPServer(("0.0.0.0", 8000), WebhookHandler)
    print("Webhook待受中: http://0.0.0.0:8000/  (Ctrl+Cで停止)")
    server.serve_forever()
