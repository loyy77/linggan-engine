#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""灵感引擎 · 本地数据服务

启动后浏览器打开 http://127.0.0.1:8765/
数据落在同目录的 data/ 下，一个 key 一个文件，JSON 格式化，方便看和备份。
只用标准库，不需要 pip install。
"""

import json
import os
import sys
import threading
import webbrowser
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

ROOT = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(ROOT, "data")

# localStorage key -> data/ 下的文件名
KEY_FILES = {
    "kg_cards_v1": "cards.json",
    "kg_cfg_v1": "cfg.json",
    "kg_collides_v1": "collides.json",
    "kg_pack_v1": "pack.json",
    "kg_bubble_v1": "bubble.json",
    "kg_view_v1": "view.json",
    "kg_theme_input_v1": "theme_input.json",
    "kg_hist_theme_v1": "hist_theme.json",
    "kg_themes_hidden_v1": "themes_hidden.json",
    "kg_models_v1": "models.json",
}
FILE_KEYS = {v: k for k, v in KEY_FILES.items()}

PORT = 8765


def ensure_dir():
    os.makedirs(DATA_DIR, exist_ok=True)


def read_key(key):
    """读一个 key，返回字符串（和 localStorage 行为一致），不存在返回 None。"""
    fn = KEY_FILES.get(key)
    if not fn:
        return None
    path = os.path.join(DATA_DIR, fn)
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.dumps(json.load(f), ensure_ascii=False)
    except Exception:
        return None


def write_key(key, raw):
    """raw 是 JSON 字符串；None 表示删除。"""
    fn = KEY_FILES.get(key)
    if not fn:
        return False
    path = os.path.join(DATA_DIR, fn)
    if raw is None:
        if os.path.exists(path):
            os.remove(path)
        return True
    try:
        value = json.loads(raw) if isinstance(raw, str) else raw
    except Exception:
        value = raw
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(value, f, ensure_ascii=False, indent=2)
        f.write("\n")
    os.replace(tmp, path)
    return True


def read_all():
    out = {}
    for key in KEY_FILES:
        v = read_key(key)
        if v is not None:
            out[key] = v
    return out


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=ROOT, **kw)

    def log_message(self, fmt, *args):
        # 只打 API 请求，静态资源太吵
        if "/api/" in (args[0] if args else ""):
            sys.stderr.write("  %s\n" % (fmt % args))

    def _json(self, code, obj):
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path.split("?")[0] == "/api/state":
            return self._json(200, read_all())
        if self.path.split("?")[0] == "/api/ping":
            return self._json(200, {"ok": True, "dir": DATA_DIR})
        return super().do_GET()

    def do_POST(self):
        path = self.path.split("?")[0]
        if path == "/api/reset":
            for fn in FILE_KEYS:
                p = os.path.join(DATA_DIR, fn)
                if os.path.exists(p):
                    os.remove(p)
            return self._json(200, {"ok": True})

        if path != "/api/state":
            return self._json(404, {"error": "not found"})

        try:
            n = int(self.headers.get("Content-Length") or 0)
            payload = json.loads(self.rfile.read(n).decode("utf-8") or "{}")
        except Exception as e:
            return self._json(400, {"error": "bad json: %s" % e})

        if not isinstance(payload, dict):
            return self._json(400, {"error": "expect object"})

        saved = []
        for key, raw in payload.items():
            if key in KEY_FILES:
                if write_key(key, raw):
                    saved.append(key)
        return self._json(200, {"ok": True, "saved": saved})

    def end_headers(self):
        # 开发时别缓存 HTML
        if self.path.endswith((".html", "/")) or "?" in self.path:
            self.send_header("Cache-Control", "no-store")
        super().end_headers()


def pick_port(start):
    import socket
    for p in range(start, start + 20):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(("127.0.0.1", p)) != 0:
                return p
    return start


def main():
    ensure_dir()
    port = pick_port(PORT)
    url = "http://127.0.0.1:%d/" % port
    print()
    print("  灵感引擎 · 本地服务")
    print("  " + url)
    print("  数据目录: " + DATA_DIR)
    print("  Ctrl+C 停止")
    print()
    threading.Timer(0.8, lambda: webbrowser.open(url)).start()
    with ThreadingHTTPServer(("127.0.0.1", port), Handler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n  已停止")


if __name__ == "__main__":
    main()
