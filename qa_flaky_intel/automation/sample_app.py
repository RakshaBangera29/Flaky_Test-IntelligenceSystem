from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread
from urllib.parse import parse_qs


HTML = """
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <title>QA Demo App</title>
    <style>
      body { background: #101418; color: #f6f8fa; font-family: Arial, sans-serif; padding: 32px; }
      main { max-width: 760px; margin: auto; display: grid; gap: 28px; }
      section { border: 1px solid #26323f; border-radius: 8px; padding: 20px; background: #141b22; }
      input, textarea, button { border-radius: 6px; border: 1px solid #344355; padding: 10px; margin: 6px 0; }
      button { background: #28d2a6; color: #07100d; font-weight: 700; cursor: pointer; }
      .result { color: #75e6ff; min-height: 24px; }
    </style>
  </head>
  <body>
    <main>
      <h1>QA Demo App</h1>
      <section>
        <h2>Login</h2>
        <input id="email" placeholder="email" />
        <input id="password" placeholder="password" type="password" />
        <button id="login-btn">Sign in</button>
        <p id="login-result" class="result"></p>
      </section>
      <section>
        <h2>Search</h2>
        <input id="search-box" placeholder="search catalog" />
        <button id="search-btn">Search</button>
        <p id="search-result" class="result"></p>
      </section>
      <section>
        <h2>Feedback</h2>
        <input id="name" placeholder="name" />
        <textarea id="message" placeholder="message"></textarea>
        <button id="submit-btn">Submit</button>
        <p id="form-result" class="result"></p>
      </section>
    </main>
    <script>
      const delay = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
      document.querySelector("#login-btn").addEventListener("click", async () => {
        await delay(120);
        document.querySelector("#login-result").textContent = "Welcome back, qa.analyst@example.com";
      });
      document.querySelector("#search-btn").addEventListener("click", async () => {
        await delay(160);
        const value = document.querySelector("#search-box").value || "all";
        document.querySelector("#search-result").textContent = `Showing results for ${value}`;
      });
      document.querySelector("#submit-btn").addEventListener("click", async () => {
        await delay(100);
        document.querySelector("#form-result").textContent = "Feedback submitted";
      });
    </script>
  </body>
</html>
"""


class DemoHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path in {"/", "/index.html"}:
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(HTML.encode("utf-8"))
            return

        self.send_response(404)
        self.end_headers()

    def do_POST(self):
        length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(length).decode("utf-8")
        fields = parse_qs(body)
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(str({"ok": True, "fields": fields}).encode("utf-8"))

    def log_message(self, format, *args):
        return


def start_demo_server(port=8765):
    server = ThreadingHTTPServer(("127.0.0.1", port), DemoHandler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server
