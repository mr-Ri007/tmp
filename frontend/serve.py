"""
serve.py — Simple static file server for the frontend.
Run: python serve.py
Then open: http://localhost:3000
"""
import http.server
import socketserver
import os

PORT = 3000
DIRECTORY = os.path.dirname(os.path.abspath(__file__))


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def end_headers(self):
        # Allow CORS from same machine (backend on 8000, frontend on 3000)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Cache-Control", "no-store, no-cache")
        super().end_headers()

    def log_message(self, format, *args):
        pass  # silence request logs; keep it clean


socketserver.TCPServer.allow_reuse_address = True
with socketserver.TCPServer(("", PORT), Handler) as httpd:
    print(f"🌐 Frontend server running at: http://localhost:{PORT}")
    print(f"📂 Serving:  {DIRECTORY}")
    print(f"📡 Backend:  http://127.0.0.1:8000")
    print("   Press Ctrl+C to stop.\n")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Server stopped.")
