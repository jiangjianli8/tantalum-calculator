#!/usr/bin/env python3
"""
Tantalum & Niobium Ore Price Server
Simple HTTP server providing a price API endpoint for the calculator.
"""

import json
import http.server
import urllib.request
import re
from datetime import datetime

PORT = 8765

class PriceHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path.startswith('/api/tantalum/price'):
            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()

            data = {
                "price": 96.0,
                "currency": "USD",
                "unit": "lb",
                "time": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "source": "默认参考价"
            }
            self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))
        elif self.path == '/' or self.path == '/index.html':
            # Serve the calculator HTML
            try:
                with open('index.html', 'r', encoding='utf-8') as f:
                    html = f.read()
                self.send_response(200)
                self.send_header('Content-Type', 'text/html; charset=utf-8')
                self.end_headers()
                self.wfile.write(html.encode('utf-8'))
            except FileNotFoundError:
                self.send_error(404, 'File not found')
        else:
            self.send_error(404)

    def log_message(self, format, *args):
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {args[0]}")

if __name__ == '__main__':
    server = http.server.HTTPServer(('0.0.0.0', PORT), PriceHandler)
    print(f'钽铌矿价格服务已启动: http://localhost:{PORT}')
    print(f'API端点: http://localhost:{PORT}/api/tantalum/price')
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print('\n服务已停止')
        server.server_close()
