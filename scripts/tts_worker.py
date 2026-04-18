#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import logging
import os
import re
import socket
import sys
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import httpx
import soundfile as sf

from miotts_server.codec import MioCodecService
from miotts_server.text import normalize_text
from miotts_server.token_parser import parse_speech_tokens

logger = logging.getLogger("tts_worker")
_JA_RE = re.compile(r"[\u3040-\u30ff\u3400-\u4dbf\u4e00-\u9fff]")


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Local Teto TTS worker")
    ap.add_argument("--socket", required=True)
    ap.add_argument("--llm-base-url", default="http://127.0.0.1:8010/v1")
    ap.add_argument("--codec-model", default="Aratako/MioCodec-25Hz-44.1kHz-v2")
    ap.add_argument("--device", default="cpu")
    ap.add_argument("--presets-dir", required=True)
    ap.add_argument("--preset-id", required=True)
    ap.add_argument("--max-tokens", type=int, default=240)
    ap.add_argument("--temperature", type=float, default=0.8)
    ap.add_argument("--top-p", type=float, default=1.0)
    ap.add_argument("--repetition-penalty", type=float, default=1.0)
    ap.add_argument("--presence-penalty", type=float, default=0.0)
    ap.add_argument("--frequency-penalty", type=float, default=0.0)
    ap.add_argument("--log-level", default="warning")
    return ap.parse_args()


class Worker:
    def __init__(self, args: argparse.Namespace) -> None:
        self.args = args
        self.client = httpx.Client(timeout=600.0)
        self.model = self._resolve_model()
        self.codec = MioCodecService(
            model_id=args.codec_model,
            device=args.device,
            presets_dir=Path(args.presets_dir),
        )
        self.codec.load()
        self.global_embedding = self.codec.load_preset_embedding(args.preset_id)

    def close(self) -> None:
        self.client.close()

    def _resolve_model(self) -> str:
        r = self.client.get(self.args.llm_base_url.rstrip("/") + "/models")
        r.raise_for_status()
        payload = r.json()
        data = payload.get("data") or []
        if not data:
            raise RuntimeError("No models returned by llama-server")
        return str(data[0]["id"])

    def ping(self) -> dict[str, Any]:
        return {"ok": True, "model": self.model}

    def synthesize(self, text: str, output_path: str) -> dict[str, Any]:
        normalized = normalize_text(text) if _JA_RE.search(text) else text.strip()
        t0 = time.perf_counter()
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": normalized}],
            "temperature": self.args.temperature,
            "top_p": self.args.top_p,
            "max_tokens": self.args.max_tokens,
            "repeat_penalty": self.args.repetition_penalty,
            "repetition_penalty": self.args.repetition_penalty,
            "presence_penalty": self.args.presence_penalty,
            "frequency_penalty": self.args.frequency_penalty,
        }
        r = self.client.post(self.args.llm_base_url.rstrip("/") + "/chat/completions", json=payload)
        r.raise_for_status()
        content = _extract_content(r.json())
        t1 = time.perf_counter()
        tokens = parse_speech_tokens(content)
        audio = self.codec.synthesize(tokens, global_embedding=self.global_embedding)
        t2 = time.perf_counter()
        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        sf.write(str(output), audio.detach().cpu().numpy(), self.codec.sample_rate, format="WAV")
        duration_sec = float(audio.numel()) / float(self.codec.sample_rate) if self.codec.sample_rate > 0 else 0.0
        return {
            "ok": True,
            "output": str(output),
            "token_count": len(tokens),
            "duration_sec": round(duration_sec, 4),
            "timings": {
                "llm_sec": round(t1 - t0, 4),
                "codec_sec": round(t2 - t1, 4),
                "total_sec": round(t2 - t0, 4),
            },
            "normalized_text": normalized,
        }


def _extract_content(payload: dict[str, Any]) -> str:
    choices = payload.get("choices")
    if not choices:
        raise RuntimeError("LLM response missing choices")
    choice = choices[0]
    if isinstance(choice, dict) and "message" in choice:
        return str(choice["message"].get("content", ""))
    return str(choice.get("text", ""))


def serve(args: argparse.Namespace) -> None:
    logging.basicConfig(level=getattr(logging, args.log_level.upper(), logging.WARNING))
    sock_path = Path(args.socket)
    sock_path.parent.mkdir(parents=True, exist_ok=True)
    if sock_path.exists():
        sock_path.unlink()

    worker = Worker(args)
    server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    server.bind(str(sock_path))
    os.chmod(sock_path, 0o600)
    server.listen(16)
    logger.info("worker listening on %s", sock_path)
    try:
        while True:
            conn, _ = server.accept()
            with conn:
                data = bytearray()
                while True:
                    chunk = conn.recv(65536)
                    if not chunk:
                        break
                    data.extend(chunk)
                if not data:
                    continue
                try:
                    req = json.loads(data.decode("utf-8"))
                    action = req.get("action")
                    if action == "ping":
                        resp = worker.ping()
                    elif action == "speak":
                        resp = worker.synthesize(str(req["text"]), str(req["output_path"]))
                    else:
                        raise RuntimeError(f"unknown action: {action}")
                except Exception as exc:  # noqa: BLE001
                    resp = {"ok": False, "error": str(exc)}
                conn.sendall(json.dumps(resp).encode("utf-8"))
    finally:
        worker.close()
        server.close()
        sock_path.unlink(missing_ok=True)


if __name__ == "__main__":
    serve(parse_args())
