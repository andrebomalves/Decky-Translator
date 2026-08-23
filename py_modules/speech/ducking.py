"""speech.ducking — Ducking via PipeWire wpctl (ADR-005)."""
from __future__ import annotations
import re
import subprocess
import logging

logger = logging.getLogger(__name__)

_DEFAULT_SINK = "@DEFAULT_SINK@"
_RE_VOLUME = re.compile(r"Volume:\s*([0-9.]+)")

def _run(cmd: list[str], timeout: float = 2.0) -> subprocess.CompletedProcess:
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except Exception as e:
        logger.warning(f"ducking: cmd {cmd} failed: {e}")
        # fabricate failure result
        cp = subprocess.CompletedProcess(cmd, returncode=1, stdout="", stderr=str(e))
        return cp

def get_volume() -> float | None:
    """Retorna volume atual 0.0-1.0 ou None se falhar."""
    cp = _run(["wpctl", "get-volume", _DEFAULT_SINK])
    if cp.returncode != 0:
        # tenta pactl fallback
        cp2 = _run(["pactl", "get-sink-volume", "@DEFAULT_SINK@"])
        if cp2.returncode == 0:
            m = re.search(r"(\d+)%", cp2.stdout)
            if m:
                try:
                    return int(m.group(1)) / 100.0
                except Exception:
                    pass
        logger.debug(f"ducking get_volume failed: {cp.stderr.strip()}")
        return None
    m = _RE_VOLUME.search(cp.stdout)
    if not m:
        logger.debug(f"ducking get_volume parse failed: {cp.stdout!r}")
        return None
    try:
        return float(m.group(1))
    except Exception:
        return None

def set_volume(level: float) -> bool:
    """level 0.0-1.0. Retorna True se ok."""
    level = max(0.0, min(1.5, float(level)))
    # wpctl set-volume usa 0.0-1.5 (0-150%)
    cp = _run(["wpctl", "set-volume", _DEFAULT_SINK, f"{level:.2f}"])
    if cp.returncode == 0:
        return True
    # fallback pactl
    pct = int(level * 100)
    cp2 = _run(["pactl", "set-sink-volume", "@DEFAULT_SINK@", f"{pct}%"])
    return cp2.returncode == 0

def duck(level_percent: int = 25) -> float | None:
    """Baixa volume para level_percent (0-100). Retorna volume original ou None."""
    orig = get_volume()
    target = max(0.0, min(1.0, level_percent / 100.0))
    ok = set_volume(target)
    if not ok:
        logger.warning("ducking: set_volume failed, continuing without ducking")
    else:
        logger.info(f"ducking: {orig} -> {target} (level {level_percent}%)")
    return orig

def restore(orig: float | None) -> None:
    """Restaura volume original. Sempre tenta, nunca levanta."""
    if orig is None:
        logger.debug("ducking restore: no orig volume, skipping")
        return
    try:
        set_volume(float(orig))
        logger.info(f"ducking restore: -> {orig}")
    except Exception as e:
        logger.warning(f"ducking restore failed: {e}")

# context manager helper
class ducked:
    def __init__(self, enabled: bool = True, level: int = 25):
        self.enabled = bool(enabled)
        self.level = int(level)
        self.orig: float | None = None
    def __enter__(self):
        if self.enabled:
            self.orig = duck(self.level)
        return self
    def __exit__(self, *exc):
        if self.enabled:
            restore(self.orig)
        return False
