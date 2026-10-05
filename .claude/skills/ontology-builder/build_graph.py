"""Build graph.html from graph.yaml, or serve a live view that updates as graph.yaml changes.

Usage:
  python3 build_graph.py <folder>                 write <folder>/graph.html (standalone, committed)
  python3 build_graph.py <folder> --serve [port]  serve a live view on http://127.0.0.1:<port> (default 8765)

In serve mode nothing is written to disk. The page polls the server and redraws whenever
graph.yaml changes, keeping node positions, so a PM can watch the graph take shape.
Stop it with Ctrl-C, then run the plain build for the final graph.html.

Requires PyYAML. The page title comes from an optional top-level `title:` in graph.yaml.
"""
import html
import json
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import yaml

TEMPLATE = (Path(__file__).parent / "graph.template.html").read_text()


def render(graph, live):
    title = html.escape(str(graph.get("title", "Ontology graph")))
    return (TEMPLATE.replace("/*TITLE*/", title)
            .replace("/*LIVE*/false", "true" if live else "false")
            .replace("/*GRAPH_JSON*/", json.dumps(graph)))


def load(path):
    graph = yaml.safe_load(path.read_text()) or {}
    graph.setdefault("nodes", [])
    graph.setdefault("edges", [])
    return graph


def serve(folder, port):
    path = folder / "graph.yaml"
    state = {"graph": load(path) if path.is_file() else {"nodes": [], "edges": []}, "mtime": 0}

    def watch():
        import time
        while True:
            try:
                m = path.stat().st_mtime
                if m != state["mtime"]:
                    state["graph"], state["mtime"] = load(path), m
            except (OSError, yaml.YAMLError) as e:
                print(f"graph.yaml not readable yet, keeping the last good graph: {str(e).splitlines()[0]}", flush=True)
                state["mtime"] = 0 if not path.is_file() else path.stat().st_mtime
            time.sleep(0.5)

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path.split("?")[0] == "/graph.json":
                body, kind = json.dumps(state["graph"]).encode(), "application/json"
            elif self.path.split("?")[0] in ("/", "/graph.html"):
                body, kind = render(state["graph"], True).encode(), "text/html; charset=utf-8"
            else:
                self.send_error(404)
                return
            self.send_response(200)
            self.send_header("Content-Type", kind)
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *args):
            pass

    threading.Thread(target=watch, daemon=True).start()
    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    print(f"live graph at http://127.0.0.1:{port} (watching {path}). Ctrl-C to stop.", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


def main():
    args = [a for a in sys.argv[1:]]
    serve_mode = "--serve" in args
    port = 8765
    if serve_mode:
        i = args.index("--serve")
        if i + 1 < len(args) and args[i + 1].isdigit():
            port = int(args.pop(i + 1))
        args.remove("--serve")
    folder = Path(args[0]) if args else Path.cwd()
    if serve_mode:
        serve(folder, port)
        return
    graph = load(folder / "graph.yaml")
    out = folder / "graph.html"
    out.write_text(render(graph, False))
    print(f"wrote {out}: {len(graph['nodes'])} nodes, {len(graph['edges'])} edges")


main()
