"""Local Web Server cho Status Investigation Agent UI.
Sử dụng thư viện chuẩn của Python (không cần pip install).
Chạy lệnh: python web/server.py
Mở trình duyệt: http://localhost:8000
"""
import http.server
import socketserver
import os
import webbrowser
from pathlib import Path

PORT = 8000
WEB_DIR = Path(__file__).resolve().parent

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(WEB_DIR), **kwargs)

def main():
    os.chdir(WEB_DIR)
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        url = f"http://localhost:{PORT}"
        print("=" * 60)
        print(f"🚀 Status Investigation Agent Dashboard đang chạy tại:")
        print(f"   👉 {url}")
        print("=" * 60)
        print("Nhấn Ctrl + C để dừng máy chủ.")
        try:
            webbrowser.open(url)
        except Exception:
            pass
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nĐã tắt máy chủ.")

if __name__ == '__main__':
    main()
