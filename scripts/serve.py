"""Static file server with HTTP Range support (PMTiles needs it; python -m http.server lacks it).
usage: python3 scripts/serve.py [port]   -> serves the repo root at http://127.0.0.1:8000/viewer/
HOST=0.0.0.0 binds all interfaces (needed for a cloud-session preview pane). "/" redirects to /viewer/."""
import http.server, os, re, sys

class H(http.server.SimpleHTTPRequestHandler):
    def send_head(self):
        if self.path in ("/", ""):
            self.send_response(302); self.send_header("Location", "/viewer/"); self.end_headers()
            return None
        rng = self.headers.get("Range")
        path = self.translate_path(self.path)
        if not rng or not os.path.isfile(path):
            return super().send_head()
        m = re.match(r"bytes=(\d*)-(\d*)$", rng)
        size = os.path.getsize(path)
        start = int(m.group(1)) if m.group(1) else size - int(m.group(2))
        end = int(m.group(2)) if m.group(1) and m.group(2) else size - 1
        end = min(end, size - 1)
        f = open(path, "rb"); f.seek(start)
        self.send_response(206)
        self.send_header("Content-Type", self.guess_type(path))
        self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
        self.send_header("Content-Length", str(end - start + 1))
        self.send_header("Accept-Ranges", "bytes")
        self.end_headers()
        self._remaining = end - start + 1
        return f

    def copyfile(self, src, dst):
        n = getattr(self, "_remaining", None)
        if n is None:
            return super().copyfile(src, dst)
        while n > 0:
            b = src.read(min(1 << 16, n))
            if not b: break
            dst.write(b); n -= len(b)

os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
host = os.environ.get("HOST", "127.0.0.1")
print(f"http://{host}:{port}/viewer/", flush=True)
http.server.ThreadingHTTPServer((host, port), H).serve_forever()
