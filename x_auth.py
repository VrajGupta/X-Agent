#!/usr/bin/env python3
"""Local X OAuth 2.0 PKCE login. Run this in a terminal you control."""

import argparse
import base64
import hashlib
import json
import os
import secrets
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path


AUTHORIZE_URL = "https://twitter.com/i/oauth2/authorize"
TOKEN_URL = "https://api.x.com/2/oauth2/token"
DEFAULT_REDIRECT_URI = "http://127.0.0.1:8765/callback"
SCOPES = "tweet.read users.read tweet.write offline.access"


def validate_redirect_uri(value):
    parsed = urllib.parse.urlsplit(value)
    if parsed.path != "/callback" or not parsed.port:
        raise RuntimeError("redirect URI must use the /callback path and include a port")
    if parsed.scheme == "http" and parsed.hostname in {"localhost", "127.0.0.1", "::1"}:
        return value
    raise RuntimeError("local OAuth callbacks must use HTTP on localhost")


def load_dotenv(path=Path(".env")):
    if not path.exists():
        return
    for raw_line in path.read_text().splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip("'\""))


def upsert_env(path, values):
    path = Path(path)
    lines = path.read_text().splitlines() if path.exists() else []
    for key, value in values.items():
        replacement = f"{key}={value}"
        for index, line in enumerate(lines):
            if line.startswith(f"{key}="):
                lines[index] = replacement
                break
        else:
            lines.append(replacement)
    path.write_text("\n".join(lines).rstrip() + "\n")
    os.chmod(path, 0o600)


def pkce_values():
    verifier = base64.urlsafe_b64encode(secrets.token_bytes(48)).rstrip(b"=").decode()
    challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b"=").decode()
    return verifier, challenge


def token_request(form, client_id, client_secret=""):
    headers = {"Content-Type": "application/x-www-form-urlencoded", "Accept": "application/json"}
    if client_secret:
        credentials = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
        headers["Authorization"] = f"Basic {credentials}"
    request = urllib.request.Request(
        TOKEN_URL,
        data=urllib.parse.urlencode(form).encode(),
        headers=headers,
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return response.read()
    except urllib.error.HTTPError as error:
        raise RuntimeError(f"X OAuth token request failed with HTTP {error.code}") from error
    except urllib.error.URLError as error:
        raise RuntimeError(f"X OAuth token request failed: {error.reason}") from error


def save_token(token, client_id, path=Path(".env")):
    values = {
        "X_CLIENT_ID": client_id,
        "X_USER_ACCESS_TOKEN": token["access_token"],
        "X_ACCESS_TOKEN_EXPIRES_AT": str(int(time.time() + token.get("expires_in", 7200))),
    }
    if token.get("refresh_token"):
        values["X_REFRESH_TOKEN"] = token["refresh_token"]
    upsert_env(path, values)
    os.environ.update(values)


def refresh_user_token(path=Path(".env")):
    refresh_token = os.environ.get("X_REFRESH_TOKEN")
    access_token = os.environ.get("X_USER_ACCESS_TOKEN")
    try:
        expires_at = float(os.environ.get("X_ACCESS_TOKEN_EXPIRES_AT", "0") or 0)
    except ValueError:
        expires_at = 0
    if not refresh_token or not os.environ.get("X_CLIENT_ID") or time.time() < expires_at - 300:
        return access_token

    form = {
        "refresh_token": refresh_token,
        "grant_type": "refresh_token",
        "client_id": os.environ["X_CLIENT_ID"],
    }
    token = json.loads(token_request(form, os.environ["X_CLIENT_ID"], os.environ.get("X_CLIENT_SECRET", "")))
    if "access_token" not in token:
        raise RuntimeError("X OAuth refresh returned no access token")
    save_token(token, os.environ["X_CLIENT_ID"], path)
    return token["access_token"]


class CallbackHandler(BaseHTTPRequestHandler):
    result = {}

    def do_GET(self):
        query = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
        type(self).result = {key: values[0] for key, values in query.items()}
        body = b"authorization received you can close this tab"
        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *_args):
        return


def authenticate(client_id, client_secret, redirect_uri, env_path):
    redirect_uri = validate_redirect_uri(redirect_uri)
    verifier, challenge = pkce_values()
    state = secrets.token_urlsafe(32)
    query = urllib.parse.urlencode(
        {
            "response_type": "code",
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "scope": SCOPES,
            "state": state,
            "code_challenge": challenge,
            "code_challenge_method": "S256",
        }
    )
    server = HTTPServer((urllib.parse.urlparse(redirect_uri).hostname, urllib.parse.urlparse(redirect_uri).port), CallbackHandler)
    server.timeout = 300
    CallbackHandler.result = {}
    thread = threading.Thread(target=server.handle_request, daemon=True)
    thread.start()
    url = f"{AUTHORIZE_URL}?{query}"
    print("opening X authorization in your browser")
    print(url)
    webbrowser.open(url)
    thread.join()
    server.server_close()

    result = CallbackHandler.result
    if result.get("state") != state:
        raise RuntimeError("X OAuth state check failed")
    if result.get("error"):
        raise RuntimeError(f"X OAuth was not approved: {result['error']}")
    if not result.get("code"):
        raise RuntimeError("X OAuth timed out waiting for the browser callback")

    token = json.loads(
        token_request(
            {
                "code": result["code"],
                "grant_type": "authorization_code",
                "client_id": client_id,
                "redirect_uri": redirect_uri,
                "code_verifier": verifier,
            },
            client_id,
            client_secret,
        )
    )
    if "access_token" not in token:
        raise RuntimeError("X OAuth returned no access token")
    save_token(token, client_id, env_path)
    print(f"authorized X and updated {env_path} without displaying the token")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--client-id")
    parser.add_argument("--client-secret")
    parser.add_argument("--redirect-uri")
    parser.add_argument("--env-file", default=".env")
    args = parser.parse_args()
    load_dotenv(Path(args.env_file))
    client_id = args.client_id or os.environ.get("X_CLIENT_ID")
    client_secret = args.client_secret if args.client_secret is not None else os.environ.get("X_CLIENT_SECRET", "")
    redirect_uri = args.redirect_uri or os.environ.get("X_REDIRECT_URI", DEFAULT_REDIRECT_URI)
    if not client_id:
        raise SystemExit("set X_CLIENT_ID or pass --client-id from your X developer app")
    authenticate(client_id, client_secret, redirect_uri, Path(args.env_file))


if __name__ == "__main__":
    try:
        main()
    except RuntimeError as error:
        raise SystemExit(f"error: {error}")
