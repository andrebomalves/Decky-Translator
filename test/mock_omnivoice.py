"""test.mock_omnivoice — Servidor HTTP mock para OmniVoice.

Servidor simples que recebe POST e retorna WAV PCM 22050Hz mono de 1s com tom 440Hz.
Útil para testes do OmniVoiceProvider sem servidor real.

Uso:
    python test/mock_omnivoice.py                    # porta 8888
    python test/mock_omnivoice.py --port 9999        # porta custom
    python test/mock_omnivoice.py --auth-token "abc" # token custom

Endpoints:
    POST /v1/audio/speech  — Recebe JSON {model, input, voice, response_format}
                              Retorna WAV binário
    GET  /                 — Health check
"""
from __future__ import annotations

import argparse
import json
import logging
import math
import struct
import sys
import wave
from http.server import HTTPServer, BaseHTTPRequestHandler
from io import BytesIO

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")
logger = logging.getLogger("mock-omnivoice")

DEFAULT_PORT = 8888
DEFAULT_AUTH_TOKEN = "test-token-1234"
DEFAULT_SAMPLE_RATE = 22050
DEFAULT_DURATION_S = 1.0
DEFAULT_FREQUENCY_HZ = 440


def generate_tone_wav(
    frequency: float = DEFAULT_FREQUENCY_HZ,
    duration: float = DEFAULT_DURATION_S,
    sample_rate: int = DEFAULT_SAMPLE_RATE,
) -> bytes:
    """Gera WAV PCM mono 22050Hz com tom senoidal."""
    n_samples = int(sample_rate * duration)
    amplitude = 0.8

    buf = BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)

        for i in range(n_samples):
            t = i / sample_rate
            value = amplitude * math.sin(2.0 * math.pi * frequency * t)
            sample = int(value * 32767)
            wf.writeframes(struct.pack("<h", sample))

    return buf.getvalue()


class MockOmniVoiceHandler(BaseHTTPRequestHandler):
    """Handler HTTP para mock do OmniVoice."""

    auth_token: str = DEFAULT_AUTH_TOKEN

    def log_message(self, format, *args):
        logger.info(f"{self.client_address[0]} - {format % args}")

    def do_GET(self):
        """Health check."""
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        resp = {"status": "ok", "service": "mock-omnivoice", "version": "1.0.0"}
        self.wfile.write(json.dumps(resp).encode("utf-8"))

    def do_POST(self):
        """Processa requisição de síntese TTS."""
        # 1) Valida Authorization header
        auth = self.headers.get("Authorization", "")
        if not auth.startswith("Bearer "):
            self._send_error(401, "Authorization header ausente ou inválido. Use: Bearer <token>")
            return

        token = auth[len("Bearer "):].strip()
        if token != self.auth_token:
            self._send_error(401, f"Token inválido: '{token[:8]}...' não corresponde")
            return

        # 2) Lê body JSON
        content_length = int(self.headers.get("Content-Length", 0))
        if content_length == 0:
            self._send_error(400, "Body vazio — envie JSON com campo 'input'")
            return

        try:
            body = self.rfile.read(content_length)
            data = json.loads(body.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            self._send_error(400, f"JSON inválido: {exc}")
            return

        text = data.get("input") or data.get("text") or ""
        if not text.strip():
            self._send_error(400, "Campo 'input' (ou 'text') vazio")
            return

        voice = data.get("voice", "default")
        logger.info(f"Sintetizando: '{text[:60]}...' voice={voice}")

        # 3) Gera WAV mock
        wav_data = generate_tone_wav()

        # 4) Retorna WAV
        self.send_response(200)
        self.send_header("Content-Type", "audio/wav")
        self.send_header("Content-Length", str(len(wav_data)))
        self.end_headers()
        self.wfile.write(wav_data)

    def _send_error(self, code: int, message: str) -> None:
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        resp = {"error": {"message": message, "code": code}}
        self.wfile.write(json.dumps(resp).encode("utf-8"))


def main():
    parser = argparse.ArgumentParser(description="Mock OmniVoice TTS server")
    parser.add_argument("--port", "-p", type=int, default=DEFAULT_PORT, help="Porta (default: 8888)")
    parser.add_argument("--auth-token", "-t", default=DEFAULT_AUTH_TOKEN,
                        help=f"Token de autenticação (default: {DEFAULT_AUTH_TOKEN})")
    parser.add_argument("--frequency", "-f", type=float, default=DEFAULT_FREQUENCY_HZ,
                        help=f"Frequência do tom em Hz (default: {DEFAULT_FREQUENCY_HZ})")
    parser.add_argument("--duration", "-d", type=float, default=DEFAULT_DURATION_S,
                        help=f"Duração em segundos (default: {DEFAULT_DURATION_S})")
    args = parser.parse_args()

    # Configura token
    MockOmniVoiceHandler.auth_token = args.auth_token

    server = HTTPServer(("0.0.0.0", args.port), MockOmniVoiceHandler)
    logger.info(f"Mock OmniVoice server rodando em http://0.0.0.0:{args.port}")
    logger.info(f"Token: {args.auth_token}")
    logger.info(f"Tom: {args.frequency}Hz, {args.duration}s")
    logger.info("Endpoints: POST /v1/audio/speech, GET /")
    logger.info("Ctrl+C para parar")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("Parando servidor...")
        server.shutdown()


if __name__ == "__main__":
    main()
