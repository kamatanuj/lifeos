#!/usr/bin/env python3
"""HTTPS server for LifeOS dashboard (needed for microphone access)."""
import http.server, ssl, os, sys, functools

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8932
CERT = '/root/Projects/JARVIS-REAL/server/certs/cert.pem'
KEY = '/root/Projects/JARVIS-REAL/server/certs/key.pem'
DIR = '/root/lifeos-prototype'

os.chdir(DIR)

handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=DIR)

httpd = http.server.HTTPServer(('0.0.0.0', PORT), handler)

context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
context.load_cert_chain(CERT, KEY)
httpd.socket = context.wrap_socket(httpd.socket, server_side=True)

print(f"LifeOS HTTPS server running on https://0.0.0.0:{PORT}")
print(f"Serving: {DIR}")
print(f"index.html exists: {os.path.exists(os.path.join(DIR, 'index.html'))}")
httpd.serve_forever()