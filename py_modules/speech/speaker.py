"""speech.speaker — Filas de reprodução TTS com ducking e prioridade."""
from __future__ import annotations

import logging
import os
import queue
import subprocess
import threading
import time
import wave
from dataclasses import dataclass, field
from enum import IntEnum
from typing import Any, Callable, Optional

logger = logging.getLogger(__name__)


class Priority(IntEnum):
    """Prioridades de fala — menor = mais urgente."""
    URGENT = 0
    HIGH = 1
    NORMAL = 2
    LOW = 3


@dataclass(order=True)
class SpeakJob:
    """Item na fila de reprodução."""
    priority: int
    text: str = field(compare=False)
    wav_path: str = field(compare=False)
    provider: Any = field(compare=False)
    ducking_config: Optional[dict] = field(compare=False, default=None)
    on_done_callback: Optional[Callable[[], None]] = field(compare=False, default=None)
    on_progress: Optional[Callable[[int, int], None]] = field(compare=False, default=None)
    job_id: str = field(compare=False, default="")


def _find_audio_player() -> Optional[str]:
    """Encontra o melhor player de áudio disponível."""
    for cmd in ("pw-play", "paplay", "aplay", "ffplay -nodisp -autoexit"):
        binary = cmd.split()[0]
        if subprocess.run(
            ["which", binary], capture_output=True
        ).returncode == 0:
            return cmd
    return None


class Speaker:
    """Reprodutor TTS com fila de prioridade, ducking e suporte a chunks.

    Uso:
        speaker = Speaker()
        speaker.start()
        speaker.speak("Olá mundo!", "/tmp/test.wav", provider)
        speaker.stop()
    """

    def __init__(self, max_queue: int = 20):
        self._queue: queue.PriorityQueue[SpeakJob] = queue.PriorityQueue(maxsize=max_queue)
        self._thread: Optional[threading.Thread] = None
        self._running = False
        self._current_process: Optional[subprocess.Popen] = None
        self._current_job: Optional[SpeakJob] = None
        self._lock = threading.Lock()
        self._player_cmd = _find_audio_player()
        self._stop_event = threading.Event()

        if not self._player_cmd:
            logger.warning("Speaker: nenhum player de áudio encontrado (pw-play/paplay/aplay)")

    def start(self) -> None:
        """Inicia a thread de processamento da fila."""
        if self._running:
            return
        self._running = True
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._process_loop, daemon=True, name="speaker-worker")
        self._thread.start()
        logger.info("Speaker: thread iniciada")

    def stop(self) -> None:
        """Para a thread e mata qualquer processo de áudio em andamento."""
        self._running = False
        self._stop_event.set()
        self._kill_current_process()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=5.0)
        self._thread = None
        logger.info("Speaker: parado")

    def speak(
        self,
        text: str,
        wav_path: str,
        provider: Any,
        ducking_config: Optional[dict] = None,
        on_done_callback: Optional[Callable[[], None]] = None,
        on_progress: Optional[Callable[[int, int], None]] = None,
        priority: int = Priority.NORMAL,
    ) -> str:
        """Enfileira uma fala. Retorna um job_id para rastreamento."""
        job_id = f"job-{int(time.time() * 1000)}-{priority}"
        job = SpeakJob(
            priority=priority,
            text=text,
            wav_path=wav_path,
            provider=provider,
            ducking_config=ducking_config,
            on_done_callback=on_done_callback,
            on_progress=on_progress,
            job_id=job_id,
        )
        try:
            self._queue.put_nowait(job)
        except queue.Full:
            logger.warning("Speaker: fila cheia, descartando job mais antigo")
            try:
                self._queue.get_nowait()
            except queue.Empty:
                pass
            self._queue.put_nowait(job)
        return job_id

    def stop_current(self) -> None:
        """Para apenas a fala em andamento (mantém fila)."""
        self._kill_current_process()
        with self._lock:
            if self._current_job and self._current_job.provider:
                try:
                    self._current_job.provider.cancel()
                except Exception:
                    pass

    def clear_queue(self) -> int:
        """Limpa a fila. Retorna quantos jobs foram descartados."""
        count = 0
        while not self._queue.empty():
            try:
                self._queue.get_nowait()
                count += 1
            except queue.Empty:
                break
        return count

    @property
    def is_speaking(self) -> bool:
        with self._lock:
            return self._current_process is not None and self._current_process.poll() is None

    @property
    def queue_size(self) -> int:
        return self._queue.qsize()

    # ── internals ─────────────────────────────────────────────────────

    def _kill_current_process(self) -> None:
        with self._lock:
            if self._current_process and self._current_process.poll() is None:
                try:
                    self._current_process.terminate()
                    self._current_process.wait(timeout=2.0)
                except Exception:
                    try:
                        self._current_process.kill()
                    except Exception:
                        pass
                self._current_process = None

    def _process_loop(self) -> None:
        """Loop principal: pega jobs da fila e reproduz."""
        logger.debug("Speaker: loop de processamento ativo")
        while self._running:
            try:
                job = self._queue.get(timeout=0.5)
            except queue.Empty:
                continue

            with self._lock:
                self._current_job = job

            try:
                self._execute_job(job)
            except Exception as exc:
                logger.error(f"Speaker: erro ao executar job {job.job_id}: {exc}")
            finally:
                with self._lock:
                    self._current_job = None
                if job.on_done_callback:
                    try:
                        job.on_done_callback()
                    except Exception as cb_exc:
                        logger.warning(f"Speaker: callback erro: {cb_exc}")

        logger.debug("Speaker: loop de processamento finalizado")

    def _execute_job(self, job: SpeakJob) -> None:
        """Executa um job: synthesize → play com ducking."""
        wav_path = job.wav_path

        # 1) Sintetiza se o provider estiver disponível
        if job.provider and job.provider.is_available():
            try:
                # Reporta progresso: etapa 1/2
                if job.on_progress:
                    job.on_progress(0, 2)
                wav_path = job.provider.synthesize(job.text, wav_path)
                if job.on_progress:
                    job.on_progress(1, 2)
            except Exception as exc:
                logger.error(f"Speaker: síntese falhou: {exc}")
                return
        elif not os.path.isfile(wav_path):
            logger.warning(f"Speaker: provider indisponível e arquivo não existe: {wav_path}")
            return

        # 2) Play com ducking
        duck_cfg = job.ducking_config or {}
        duck_enabled = duck_cfg.get("enabled", True)
        duck_level = duck_cfg.get("level_percent", 25)

        orig_volume = None
        try:
            if duck_enabled:
                from .ducking import duck
                orig_volume = duck(duck_level)

            self._play_wav(wav_path)
            if job.on_progress:
                job.on_progress(2, 2)

        finally:
            if duck_enabled and orig_volume is not None:
                try:
                    from .ducking import restore
                    restore(orig_volume)
                except Exception as exc:
                    logger.warning(f"Speaker: restore volume falhou: {exc}")

    def _play_wav(self, wav_path: str) -> None:
        """Reproduz arquivo WAV usando o player disponível."""
        if not self._player_cmd:
            logger.warning("Speaker: nenhum player disponível, ignorando reprodução")
            return

        if not os.path.isfile(wav_path):
            logger.warning(f"Speaker: arquivo não encontrado: {wav_path}")
            return

        cmd_parts = self._player_cmd.split()
        cmd = cmd_parts + [wav_path]

        try:
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            with self._lock:
                self._current_process = proc

            # espera terminar ou stop
            while proc.poll() is None:
                if self._stop_event.is_set() or not self._running:
                    try:
                        proc.terminate()
                    except Exception:
                        pass
                    break
                time.sleep(0.05)

            if proc.returncode and proc.returncode not in (0, -15, -9):
                logger.warning(f"Speaker: player retornou código {proc.returncode}")

        except FileNotFoundError:
            logger.error(f"Speaker: player não encontrado: {cmd_parts[0]}")
        except Exception as exc:
            logger.error(f"Speaker: erro ao reproduzir: {exc}")
        finally:
            with self._lock:
                self._current_process = None
