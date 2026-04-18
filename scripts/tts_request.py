#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import socket
import sys


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Send a request to local Teto TTS worker")
    ap.add_argument("--socket", required=True)
    ap.add_argument("--ping", action="store_true")
    ap.add_argument("--text")
    ap.add_argument("--output")
    return ap.parse_args()


def main() -> None:
    args = parse_args()
    if args.ping:
        payload = {"action": "ping"}
    else:
        if not args.text or not args.output:
            raise SystemExit("--text and --output are required unless --ping is used")
        payload = {"action": "speak", "text": args.text, "output_path": args.output}
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as sock:
        sock.connect(args.socket)
        sock.sendall(json.dumps(payload).encode("utf-8"))
        sock.shutdown(socket.SHUT_WR)
        data = bytearray()
        while True:
            chunk = sock.recv(65536)
            if not chunk:
                break
            data.extend(chunk)
    if not data:
        raise SystemExit("empty response from worker")
    resp = json.loads(data.decode("utf-8"))
    if not resp.get("ok"):
        raise SystemExit(resp.get("error", "worker request failed"))
    print(json.dumps(resp, ensure_ascii=False))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:  # noqa: BLE001
        print(str(exc), file=sys.stderr)
        raise
