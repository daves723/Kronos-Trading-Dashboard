import http.server
import json
import os
import sys
import io
import urllib.parse
import contextlib

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

import bridge_search
import bridge_chart
import bridge_agent_v4

PORT = 3456

def call_search(q):
    f = io.StringIO()
    with contextlib.redirect_stdout(f):
        bridge_search.search(q)
    out = f.getvalue().strip()
    if out:
        return out
    # Fallback: try tushare backup
    f2 = io.StringIO()
    with contextlib.redirect_stdout(f2):
        bridge_search.tushare_backup_search(q)
    out2 = f2.getvalue().strip()
    return out2 if out2 else json.dumps({"results":[]})

def call_chart(code):
    import subprocess, json as _json
    python_exe = r"C:\Users\Admin\AppData\Local\Programs\Python\Python312\python.exe"
    script = os.path.join(ROOT, "bridge_chart.py")
    try:
        result = subprocess.run([python_exe, script, code], capture_output=True, text=True, cwd=ROOT, timeout=60)
        for line in result.stdout.split("\n"):
            line = line.strip()
            if line.startswith("{"):
                d = _json.loads(line)
                # Override with correct model name
                if "segments" in d and d["segments"]:
                    d["model"] = "Kronos-small"
                return _json.dumps(d, ensure_ascii=False)
        return _json.dumps({"error": "no json in output"})
    except Exception as e:
        return _json.dumps({"error": str(e)})
def call_agent(code):
    f = io.StringIO()
    with contextlib.redirect_stdout(f):
        bridge_agent_v4.analyze(code)
    raw = f.getvalue().strip()
    for line in raw.split(chr(10)):
        line = line.strip()
        if line.startswith('{'):
            return line
    return raw

class Handler(http.server.BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        params = urllib.parse.parse_qs(parsed.query)
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        
        try:
            if path == "/api/search":
                q = params.get("q", [""])[0]
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(call_search(q).encode("utf-8"))
            elif path == "/api/chart":
                code = params.get("code", [""])[0]
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(call_chart(code).encode("utf-8"))
            elif path == "/api/analyze":
                code = params.get("code", [""])[0]
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(call_agent(code).encode("utf-8"))
            else:
                fp = os.path.join(ROOT, "index.html") if path == "/" else os.path.join(ROOT, path.lstrip("/"))
                if os.path.isfile(fp):
                    ext = os.path.splitext(fp)[1]
                    mime = "application/javascript" if ext == ".js" else "text/html"
                    self.send_header("Content-Type", f"{mime}; charset=utf-8")
                    self.end_headers()
                    with open(fp, "rb") as f:
                        self.wfile.write(f.read())
                else:
                    self.send_header("Content-Type", "text/html; charset=utf-8")
                    self.end_headers()
                    with open(os.path.join(ROOT, "index.html"), "rb") as f:
                        self.wfile.write(f.read())
        except Exception as e:
            try:
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps({"error":str(e)}).encode("utf-8"))
            except:
                self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(json.dumps({"error":str(e)}).encode("utf-8"))

    def log_message(self, format, *args):
        pass

if __name__ == "__main__":
    print(f"Kronos Dashboard: http://localhost:{PORT}")
    http.server.HTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
