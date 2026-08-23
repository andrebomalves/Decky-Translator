"""EdgeTTS provider - TTS online via edge-tts (Microsoft Edge)."""
import asyncio
import logging
import threading
import os
from typing import Optional

from .base import TTSProvider

logger = logging.getLogger(__name__)


class EdgeTTSProvider(TTSProvider):
    """Provider online via edge-tts (vozes neurais Microsoft).

    Grava MP3 retornado pelo edge-tts em wav_path (paplay/pw-play suportam MP3).
    Mensagens de erro sao amigaveis em PT-BR, nunca vaza stack/key.
    """

    DEFAULT_VOICE = "pt-BR-FranciscaNeural"
    DEFAULT_TIMEOUT = 15

    def __init__(
        self,
        voice: str = DEFAULT_VOICE,
        rate: str = "+0%",
        volume: str = "+0%",
        timeout: int = DEFAULT_TIMEOUT,
    ):
        self.voice = voice
        self.rate = rate
        self.volume = volume
        self.timeout = int(timeout)
        self._cancel_requested = False

    # -- TTSProvider API --

    def is_available(self) -> bool:
        try:
            import edge_tts  # noqa: F401
            return True
        except Exception:
            return False

    def cancel(self) -> None:
        self._cancel_requested = True

    def synthesize(self, text: str, wav_path: str) -> str:
        if not text or not text.strip():
            raise ValueError("Texto vazio - nada para sintetizar")
        if not self.is_available():
            raise RuntimeError(
                "Edge TTS nao disponivel: pacote 'edge-tts' nao instalado. "
                "Instale com: pip install edge-tts"
            )
        self._cancel_requested = False
        try:
            self._run_synthesize(text, wav_path)
        except RuntimeError:
            raise
        except Exception as exc:
            msg = str(exc).lower()
            if "noaudioreceived" in msg or "no audio" in msg:
                raise RuntimeError(
                    "Edge TTS nao retornou audio - texto pode ser invalido ou voz indisponivel"
                ) from exc
            if "unexpected" in msg or "websocket" in msg:
                raise RuntimeError(f"Falha de conexao com Edge TTS: {exc}. Verifique sua internet.") from exc
            raise RuntimeError(f"Erro no Edge TTS: {exc}") from exc

        if self._cancel_requested:
            try:
                if os.path.exists(wav_path):
                    os.remove(wav_path)
            except Exception:
                pass
            raise RuntimeError("Sintese cancelada pelo usuario")
        return wav_path

    # -- internal --

    def _run_synthesize(self, text: str, wav_path: str) -> None:
        try:
            asyncio.get_running_loop()
            has_loop = True
        except RuntimeError:
            has_loop = False

        if has_loop:
            exc_holder: list = []

            def _thread_target():
                try:
                    asyncio.run(asyncio.wait_for(self._async_synthesize(text, wav_path), timeout=self.timeout))
                except Exception as e:
                    exc_holder.append(e)

            t = threading.Thread(target=_thread_target, daemon=True)
            t.start()
            t.join(timeout=self.timeout + 5)
            if t.is_alive():
                raise RuntimeError(f"Tempo limite excedido ({self.timeout}s) ao conectar no Edge TTS")
            if exc_holder:
                e = exc_holder[0]
                if isinstance(e, asyncio.TimeoutError):
                    raise RuntimeError(f"Tempo limite excedido ({self.timeout}s) ao sintetizar com Edge TTS") from e
                raise e
        else:
            try:
                asyncio.run(asyncio.wait_for(self._async_synthesize(text, wav_path), timeout=self.timeout))
            except asyncio.TimeoutError as e:
                raise RuntimeError(f"Tempo limite excedido ({self.timeout}s) ao sintetizar com Edge TTS") from e

    async def _async_synthesize(self, text: str, wav_path: str) -> None:
        import edge_tts
        communicate = edge_tts.Communicate(text, self.voice, rate=self.rate, volume=self.volume)
        os.makedirs(os.path.dirname(os.path.abspath(wav_path)) or ".", exist_ok=True)
        with open(wav_path, "wb") as f:
            async for chunk in communicate.stream():
                if self._cancel_requested:
                    break
                if chunk.get("type") == "audio":
                    data = chunk.get("data")
                    if data:
                        f.write(data)

    # -- runtime config sem restart --

    def configure(
        self,
        voice: Optional[str] = None,
        rate: Optional[str] = None,
        volume: Optional[str] = None,
        timeout: Optional[int] = None,
    ) -> None:
        if voice is not None:
            self.voice = voice
        if rate is not None:
            self.rate = rate
        if volume is not None:
            self.volume = volume
        if timeout is not None:
            self.timeout = int(timeout)

    def set_voice(self, voice: str) -> None:
        self.voice = voice
