"""TTSProvider ABC - contrato offline/online."""
from abc import ABC, abstractmethod


class TTSProvider(ABC):
    """Contrato minimo para provedores TTS."""

    @abstractmethod
    def synthesize(self, text: str, wav_path: str) -> str:
        """Sintetiza texto para WAV. Retorna wav_path. Deve ser sincrono e bloqueante."""
        raise NotImplementedError

    def cancel(self) -> None:
        """Cancela sintese em andamento (no-op por padrao)."""
        return None

    @abstractmethod
    def is_available(self) -> bool:
        """True se provider pode sintetizar sem erro (modelo/runtime disponiveis)."""
        raise NotImplementedError
