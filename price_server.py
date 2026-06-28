#!/usr/bin/env python3
"""
Tantalum & Niobium Ore Price Server with SMM scraper integration.
Reads from price_cache.json for latest prices.
"""

import json
import os
import http.server
import urllib.request
from datetime import datetime

PORT = 8765

class PriceHandler(http.server.BaseHTTPRequestHandler):

    def _get_price_data(self):
        """Read latest price from cache file"""
        try:
            cache_path = os.path.join(os.path.dirname(__file__), "price_cache.json")
            if os.path.exists(cache_path):
                with open(cache_path, "r", encoding="utf-8") as f:
                    cache = json.load(f)
                price = cache.get("defaultPrice", 232.5)
                source = "SMM" if cache.get("success") else "SMM"
                ts = cache.get("timestamp", "")
                return price, source, ts
        except Exception:
            pass
        return 232.5, "默认参考价", ""

    def do_GET(self):
        if self.path == "/api/refresh":
            price, source, ts = 232.5, "刷新中...", ""
            try:
                import subprocess
                scraper = os.path.join(os.path.dirname(__file__), "smm_scraper.js")
                result = subprocess.run(
                    ["node", scraper, "--json"],
                    capture_output=True, text=True, timeout=90,
                    cwd=os.path.dirname(__file__)
                )
                output = json.loads(result.stdout.strip())
                price = output.get("defaultPrice", 232.5)
                source = "SMM实时" if output.get("success") else "SMM-默认"
                ts = output.get("timestamp", "")
            except Exception as e:
                source = f"刷新异常:{str(e)[:40]}"

            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            data = {"price": price, "currency": "USD", "unit": "lb", "time": ts, "source": source}
            self.wfile.write(json.dumps(data, ensure_ascii=False).encode("utf-8"))
            return

        if self.path.startswith("/api/tantalum/price"):
            price, source, ts = self._get_price_data()
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            data = {
                "price": price,
                "currency": "USD",
                "unit": "lb",
                "time": ts or datetime.now().strftime("%Y-%m-%d %H:%M"),
                "source": source,
            }
            self.wfile.write(json.dumps(data, ensure_ascii=False).encode("utf-8"))
        elif self.path == "/" or self.path == "/index.html":
            try:
                with open("index.html", "r", encoding="utf-8") as f:
                    html = f.read()
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
                self.wfile.write(html.encode("utf-8"))
            except FileNotFoundError:
                self.send_error(404, "File not found")
        else:
            self.send_error(404)

    def log_message(self, format, *args):
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {args[0]}")


if __name__ == "__main__":
    # Generate initial cache if not exists
    cache_path = os.path.join(os.path.dirname(__file__), "price_cache.json")
    if not os.path.exists(cache_path):
        with open(cache_path, "w") as f:
            json.dump({"success": False, "timestamp": "", "defaultPrice": 232.5}, f)
        print("初始化 price_cache.json")

    server = http.server.HTTPServer(("0.0.0.0", PORT), PriceHandler)
    print(f"SMM 钽铌矿价格服务: http://localhost:{PORT}")
    print(f"API: http://localhost:{PORT}/api/tantalum/price")
    print(f"刷新: http://localhost:{PORT}/api/refresh")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n服务已停止")
        server.server_close()
