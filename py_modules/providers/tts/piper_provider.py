"""Piper TTS provider — síntese offline via piper-tts ou onnxruntime."""
from __future__ import annotations

import logging
import os
import shutil
import subprocess
import wave
from typing import Optional

import numpy as np

from .base import TTSProvider

logger = logging.getLogger(__name__)

_DEFAULT_VOICE = "pt_BR-faber-medium"
_DEFAULT_SPEED = 1.0  # length_scale = 1.0 / speed
_DEFAULT_SAMPLE_RATE = 22050


class PiperTTSProvider(TTSProvider):
    """Provider offline via Piper TTS (onnx models).

    Configuração:
      - voice: nome do modelo (default: pt_BR-faber-medium)
      - speed: multiplicador de velocidade (1.0 = normal)
      - model_dir: diretório com modelo .onnx + .json
        Busca em: model_dir, defaults/models/, DOWNLOAD_DIR
      - download_dir: diretório para download automático

    Se piper/onnxruntime indisponível, fallback para eSpeak com warning.
    synthesize() gera WAV 22050Hz mono.
    """

    DOWNLOAD_DIR = os.environ.get(
        "PIPER_MODEL_DIR",
        os.path.join(os.path.expanduser("~"), ".local", "share", "piper-tts", "models"),
    )

    def __init__(
        self,
        voice: str = _DEFAULT_VOICE,
        speed: float = _DEFAULT_SPEED,
        model_dir: Optional[str] = None,
        download_dir: Optional[str] = None,
        sample_rate: int = _DEFAULT_SAMPLE_RATE,
    ):
        self.voice = voice
        self.speed = max(0.1, min(5.0, float(speed)))
        self.model_dir = model_dir or ""
        self.download_dir = download_dir or self.DOWNLOAD_DIR
        self.sample_rate = sample_rate
        self._cancel_requested = False
        self._model_path: Optional[str] = None
        self._config_path: Optional[str] = None
        self._resolve_model_paths()

    # ── model resolution ──────────────────────────────────────────────

    def _resolve_model_paths(self) -> None:
        """Encontra o modelo .onnx e config .json para self.voice."""
        candidates = [
            self.model_dir,
            os.path.join("defaults", "models"),
            os.path.join("py_modules", "providers", "tts", "defaults", "models"),
            self.download_dir,
        ]
        for base in candidates:
            if not base:
                continue
            onnx = os.path.join(base, f"{self.voice}.onnx")
            json_cfg = os.path.join(base, f"{self.voice}.onnx.json")
            if os.path.isfile(onnx):
                self._model_path = onnx
                self._config_path = json_cfg if os.path.isfile(json_cfg) else None
                logger.debug(f"Modelo encontrado: {onnx}")
                return

        # tenta subdiretórios
        for base in candidates:
            if not base or not os.path.isdir(base):
                continue
            sub = os.path.join(base, self.voice)
            onnx = os.path.join(sub, f"{self.voice}.onnx")
            if os.path.isfile(onnx):
                self._model_path = onnx
                json_cfg = os.path.join(sub, f"{self.voice}.onnx.json")
                self._config_path = json_cfg if os.path.isfile(json_cfg) else None
                logger.debug(f"Modelo encontrado: {onnx}")
                return

        self._model_path = None
        self._config_path = None

    # ── TTSProvider API ───────────────────────────────────────────────

    def is_available(self) -> bool:
        """True se modelo .onnx existe E (piper CLI ou onnxruntime disponível)."""
        if not self._model_path:
            return False
        if shutil.which("piper"):
            return True
        try:
            import onnxruntime  # noqa: F401
            return True
        except ImportError:
            pass
        return False

    def cancel(self) -> None:
        self._cancel_requested = True

    def synthesize(self, text: str, wav_path: str) -> str:
        if not text or not text.strip():
            raise ValueError("Texto vazio - nada para sintetizar")
        if not self.is_available():
            raise RuntimeError(
                "Piper TTS indisponível: modelo não encontrado ou runtime ausente. "
                f"Modelo esperado: {self.voice}.onnx em {self.download_dir}"
            )

        self._cancel_requested = False
        os.makedirs(os.path.dirname(os.path.abspath(wav_path)) or ".", exist_ok=True)

        if shutil.which("piper"):
            self._synthesize_cli(text, wav_path)
        else:
            self._synthesize_onnx(text, wav_path)

        if self._cancel_requested:
            try:
                os.remove(wav_path)
            except OSError:
                pass
            raise RuntimeError("Sintese cancelada pelo usuario")

        return wav_path

    # ── piper CLI ─────────────────────────────────────────────────────

    def _synthesize_cli(self, text: str, wav_path: str) -> None:
        length_scale = 1.0 / self.speed
        model = self._model_path or ""
        cmd = [
            "piper",
            "--model", model,
            "--output_file", wav_path,
            "--length_scale", str(length_scale),
            "--sentence_silence", "0.2",
        ]
        if self._config_path:
            cmd.extend(["--config", self._config_path])

        try:
            proc = subprocess.run(
                cmd,
                input=text.encode("utf-8"),
                capture_output=True,
                timeout=30,
            )
            if proc.returncode != 0:
                stderr = proc.stderr.decode("utf-8", errors="replace").strip()
                raise RuntimeError(f"Piper CLI falhou (rc={proc.returncode}): {stderr}")
        except subprocess.TimeoutExpired:
            raise RuntimeError("Piper CLI timeout (30s)")

    # ── onnxruntime direto ────────────────────────────────────────────

    def _synthesize_onnx(self, text: str, wav_path: str) -> None:
        try:
            import onnxruntime as ort
        except ImportError:
            raise RuntimeError(
                "Nem piper CLI nem onnxruntime disponíveis. "
                "Instale: pip install piper-tts ou pip install onnxruntime"
            )

        sess = ort.InferenceSession(self._model_path or "")
        input_names = [i.name for i in sess.get_inputs()]

        phoneme_ids = self._text_to_phoneme_ids(text)

        audio_chunks: list[np.ndarray] = []
        window_size = 100
        for i in range(0, len(phoneme_ids), window_size):
            if self._cancel_requested:
                break
            window = phoneme_ids[i : i + window_size]
            feed: dict = {}
            for name in input_names:
                if "input" in name.lower() and "id" in name.lower():
                    feed[name] = [window]
                elif "length" in name.lower():
                    feed[name] = [len(window)]
                else:
                    feed[name] = [[1.0 / self.speed]]

            outputs = sess.run(None, feed)
            if outputs:
                raw = outputs[0]
                audio_chunks.append(
                    raw.flatten() if hasattr(raw, "flatten") else np.asarray(raw).flatten()
                )

        if not audio_chunks:
            raise RuntimeError("Piper onnx não gerou áudio")

        audio = np.concatenate(audio_chunks)
        self._write_wav(audio, wav_path)

    def _text_to_phoneme_ids(self, text: str) -> list[int]:
        """Converte texto em phoneme IDs para Piper."""
        # tenta piper_phonemizer
        try:
            from piper_phonemize import phonemize  # type: ignore
            phonemes = phonemize(text, language="pt_BR")
            return self._phonemes_to_ids(phonemes)
        except ImportError:
            pass

        # fallback: espeak-ng para fonemas
        try:
            proc = subprocess.run(
                ["espeak-ng", "-v", "pt-br", "--phonout=-", text],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if proc.returncode == 0 and proc.stdout.strip():
                return self._phonemes_to_ids(proc.stdout.strip())
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass

        logger.warning("Piper: nenhuma engine de fonemas disponível, usando fallback ASCII")
        return [ord(c) % 256 for c in text[:200]]

    def _phonemes_to_ids(self, phonemes: str) -> list[int]:
        """Mapeia string de fonemas para IDs numéricos usando o config do modelo."""
        if self._config_path and os.path.isfile(self._config_path):
            try:
                import json
                with open(self._config_path) as f:
                    cfg = json.load(f)
                id_map = cfg.get("phoneme_id_map", {})
                ids: list[int] = []
                for ch in phonemes:
                    mapped = id_map.get(ch, None)
                    if mapped:
                        ids.extend(mapped if isinstance(mapped, list) else [mapped])
                    elif ch == " ":
                        ids.append(0)
                return ids if ids else [0]
            except Exception:
                pass

        return [ord(c) % 256 for c in phonemes[:200]]

    # ── WAV output ────────────────────────────────────────────────────

    def _write_wav(self, audio: np.ndarray, wav_path: str) -> None:
        """Escreve array de áudio float32 como WAV 22050Hz mono."""
        if audio.dtype != np.float32:
            audio = audio.astype(np.float32)
        peak = np.max(np.abs(audio)) if len(audio) > 0 else 1.0
        if peak > 0:
            audio = audio / peak * 0.95

        samples = (audio * 32767).astype(np.int16)

        with wave.open(wav_path, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(self.sample_rate)
            wf.writeframes(samples.tobytes())

    # ── config ────────────────────────────────────────────────────────

    def configure(
        self,
        voice: Optional[str] = None,
        speed: Optional[float] = None,
        model_dir: Optional[str] = None,
        download_dir: Optional[str] = None,
    ) -> None:
        if voice is not None:
            self.voice = voice
            self._resolve_model_paths()
        if speed is not None:
            self.speed = max(0.1, min(5.0, float(speed)))
        if model_dir is not None:
            self.model_dir = model_dir
            self._resolve_model_paths()
        if download_dir is not None:
            self.download_dir = download_dir

    def set_voice(self, voice: str) -> None:
        self.voice = voice
        self._resolve_model_paths()
