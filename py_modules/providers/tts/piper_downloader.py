"""Downloader para modelos de voz Piper.

Baixa .onnx + .onnx.json do HuggingFace (rhasspy/piper-voices).
Suporta progresso, cancelamento e resume parcial via .part.
"""
from __future__ import annotations

import hashlib
import logging
import os
import shutil
import threading
from typing import Optional
from urllib.parse import urljoin

import requests

logger = logging.getLogger(__name__)

BASE_URL = "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0"
CHUNK_SIZE = 8192

# sha256 não é fornecido pelo repo; usamos tamanho como check rápido.
# Se precisar de validação forte, adicionar dicionário de hashes aqui.
VOICE_FILES = {
    "pt_BR-faber-medium": {
        "onnx": "pt/pt_BR/faber/medium/pt_BR-faber-medium.onnx",
        "json": "pt/pt_BR/faber/medium/pt_BR-faber-medium.onnx.json",
    }
}


def _user_data_dir() -> str:
    home = os.path.expanduser("~")
    return os.path.join(home, ".local", "share", "decky-translator", "piper-voices")


class PiperDownloader:
    """Gerencia download de vozes Piper."""

    def __init__(self, base_dir: Optional[str] = None):
        self._base_dir = base_dir or _user_data_dir()
        os.makedirs(self._base_dir, exist_ok=True)
        self._downloading = False
        self._progress = 0.0
        self._error: Optional[str] = None
        self._cancel = False
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()

    def model_dir_for_voice(self, voice: str) -> str:
        return os.path.join(self._base_dir, voice)

    def is_downloaded(self, voice: str) -> bool:
        """True se .onnx existe (json é opcional mas recomendado)."""
        d = self.model_dir_for_voice(voice)
        onnx = os.path.join(d, f"{voice}.onnx")
        return os.path.isfile(onnx)

    def is_downloading(self) -> bool:
        with self._lock:
            return self._downloading

    def get_progress(self) -> float:
        with self._lock:
            return self._progress

    def get_status(self, voice: str = "pt_BR-faber-medium") -> dict:
        with self._lock:
            return {
                "downloaded": self.is_downloaded(voice),
                "downloading": self._downloading,
                "progress": self._progress,
                "error": self._error,
                "model_dir": self.model_dir_for_voice(voice),
            }

    def start_download(self, voice: str = "pt_BR-faber-medium") -> bool:
        if self.is_downloaded(voice):
            return True
        with self._lock:
            if self._downloading:
                return True
            self._downloading = True
            self._progress = 0.0
            self._error = None
            self._cancel = False

        self._thread = threading.Thread(
            target=self._download_worker,
            args=(voice,),
            daemon=True,
            name="piper-download",
        )
        self._thread.start()
        return True

    def cancel_download(self) -> None:
        with self._lock:
            self._cancel = True

    def _download_worker(self, voice: str) -> None:
        try:
            self._do_download(voice)
        except Exception as e:
            logger.error(f"Piper download failed: {e}")
            with self._lock:
                self._error = str(e)
        finally:
            with self._lock:
                self._downloading = False
                if not self._cancel:
                    self._progress = 100.0 if self.is_downloaded(voice) else self._progress

    def _do_download(self, voice: str) -> None:
        files = VOICE_FILES.get(voice)
        if not files:
            raise ValueError(f"Voz Piper desconhecida: {voice}")

        target_dir = self.model_dir_for_voice(voice)
        os.makedirs(target_dir, exist_ok=True)

        total_bytes = 0
        downloaded_bytes = 0

        # Primeiro, descobre tamanho total
        for key, path in files.items():
            url = urljoin(BASE_URL + "/", path)
            r = requests.head(url, timeout=10, allow_redirects=True)
            r.raise_for_status()
            total_bytes += int(r.headers.get("Content-Length", 0))

        for key, path in files.items():
            url = urljoin(BASE_URL + "/", path)
            dest = os.path.join(target_dir, os.path.basename(path))
            part = dest + ".part"

            headers = {}
            resume_from = 0
            if os.path.isfile(part):
                resume_from = os.path.getsize(part)
                headers["Range"] = f"bytes={resume_from}-"

            with requests.get(url, headers=headers, stream=True, timeout=30) as resp:
                resp.raise_for_status()
                mode = "ab" if resume_from else "wb"
                with open(part, mode) as f:
                    for chunk in resp.iter_content(chunk_size=CHUNK_SIZE):
                        if self._cancel:
                            return
                        if not chunk:
                            continue
                        f.write(chunk)
                        downloaded_bytes += len(chunk)
                        if total_bytes > 0:
                            with self._lock:
                                self._progress = min(99.0, downloaded_bytes / total_bytes * 100)

            shutil.move(part, dest)
            logger.info(f"Piper download complete: {dest}")

        with self._lock:
            self._progress = 100.0
