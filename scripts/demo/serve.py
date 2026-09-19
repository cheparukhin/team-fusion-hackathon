"""Serve the repository locally for cached demo and provenance links."""
import argparse,functools,http.server
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--port',type=int,default=8000);p.add_argument('--host',default='127.0.0.1');a=p.parse_args()
root=Path(__file__).resolve().parents[2]
print(f'Open http://{a.host}:{a.port}/demo/',flush=True)
http.server.ThreadingHTTPServer((a.host,a.port),functools.partial(http.server.SimpleHTTPRequestHandler,directory=str(root))).serve_forever()
