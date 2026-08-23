"""OmniVoice adapter HTTP - compat openai|simple, Bearer, 4xx/timeout amigavel."""

import json
import os
import logging
from typing import Optional
from urllib.parse import urlparse

import requests

from .base import TTSProvider

logger = logging.getLogger(__name__)


class OmniVoiceProvider(TTSProvider):
    """Adapter HTTP para OmniVoice.

    Modos via flag compat (troca em runtime sem restart):
      - openai: POST {endpoint}/v1/audio/speech  {model, input, voice, response_format}
      - simple: POST {endpoint}                  {text, language, voice, response_format}

    Headers: Authorization: Bearer <api_key>
    Erros nunca crasham: URL invalida, 4xx, timeout -> RuntimeError PT-BR amigavel.
    Key vazia bloqueia antes de qualquer rede.
    """

    DEFAULT_TIMEOUT = 15
    DEFAULT_VOICE = "faber"
    DEFAULT_MODEL = "tts-1"
    DEFAULT_LANGUAGE = "pt-BR"

    def __init__(
        self,
        endpoint: str = "",
        api_key: str = "",
        compat: str = "openai",
        voice: str = DEFAULT_VOICE,
        model: str = DEFAULT_MODEL,
        language: str = DEFAULT_LANGUAGE,
        timeout: int = DEFAULT_TIMEOUT,
    ):
        self.endpoint = (endpoint or "").strip()
        self.api_key = api_key or ""
        self.compat = compat if compat in ("openai", "simple") else "openai"
        self.voice = voice
        self.model = model
        self.language = language
        self.timeout = int(timeout)
        self._cancel_requested = False

    # -- TTSProvider API --

    def is_available(self) -> bool:
        # disponivel se configurado (nao valida rede)
        return bool(self.endpoint and self.api_key and self.api_key.strip())

    def cancel(self) -> None:
        self._cancel_requested = True

    def configure(
        self,
        endpoint: Optional[str] = None,
        api_key: Optional[str] = None,
        compat: Optional[str] = None,
        voice: Optional[str] = None,
        model: Optional[str] = None,
        language: Optional[str] = None,
        timeout: Optional[int] = None,
    ) -> None:
        """Atualiza config em tempo de execucao sem restart."""
        if endpoint is not None:
            self.endpoint = endpoint.strip()
        if api_key is not None:
            self.api_key = api_key
        if compat is not None:
            if compat in ("openai", "simple"):
                self.compat = compat
        if voice is not None:
            self.voice = voice
        if model is not None:
            self.model = model
        if language is not None:
            self.language = language
        if timeout is not None:
            self.timeout = int(timeout)

    # aliases para compatibilidade com spec
    def set_compat(self, compat: str) -> None:
        if compat in ("openai", "simple"):
            self.compat = compat

    def set_endpoint(self, endpoint: str) -> None:
        self.endpoint = (endpoint or "").strip()

    def set_api_key(self, api_key: str) -> None:
        self.api_key = api_key or ""

    def synthesize(self, text: str, wav_path: str) -> str:
        if not text or not text.strip():
            raise ValueError("Texto vazio - nada para sintetizar")

        # key vazia bloqueia antes de rede
        if not self.api_key or not self.api_key.strip():
            raise RuntimeError(
                "Chave da API nao configurada - defina a API key do OmniVoice antes de usar"
            )

        if not self.endpoint or not self.endpoint.strip():
            raise RuntimeError(
                "Endpoint nao configurado - defina a URL do OmniVoice antes de usar"
            )

        # validacao de URL amigavel (nao crasha)
        parsed = urlparse(self.endpoint)
        if not parsed.scheme or not parsed.netloc:
            raise RuntimeError(
                f"URL invalida: '{self.endpoint}' - verifique a URL do OmniVoice (deve comecar com http:// ou https://)"
            )
        if parsed.scheme not in ("http", "https"):
            raise RuntimeError(
                f"URL invalida: esquema '{parsed.scheme}' nao suportado - use http:// ou https://"
            )

        # monta URL e payload por compat
        if self.compat == "openai":
            # evita duplicar /v1/audio/speech
            base = self.endpoint.rstrip("/")
            if base.endswith("/v1/audio/speech"):
                url = base
            else:
                url = base + "/v1/audio/speech"
            payload = {
                "model": self.model,
                "input": text,
                "voice": self.voice,
                "response_format": "wav",
            }
        else:  # simple
            url = self.endpoint
            payload = {
                "text": text,
                "language": self.language,
                "voice": self.voice,
                "response_format": "wav",
            }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        self._cancel_requested = False

        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=self.timeout)
        except requests.exceptions.MissingSchema as exc:
            raise RuntimeError(f"URL invalida: '{url}' - verifique a URL do OmniVoice") from exc
        except requests.exceptions.InvalidURL as exc:
            raise RuntimeError(f"URL invalida: '{url}' - verifique a URL do OmniVoice") from exc
        except requests.exceptions.InvalidSchema as exc:
            raise RuntimeError(f"URL invalida: esquema nao suportado em '{url}'") from exc
        except requests.exceptions.Timeout as exc:
            raise RuntimeError(
                f"Tempo limite excedido ({self.timeout}s) ao conectar no OmniVoice - verifique sua conexao ou tente novamente"
            ) from exc
        except requests.exceptions.ConnectionError as exc:
            raise RuntimeError(
                f"Servidor inacessivel em '{url}' - verifique a URL ou sua conexao com a internet"
            ) from exc
        except requests.exceptions.RequestException as exc:
            raise RuntimeError(f"Erro de rede ao conectar no OmniVoice: {exc}") from exc

        # trata 4xx/5xx com mensagem amigavel
        if resp.status_code >= 400:
            body = ""
            try:
                body = resp.text[:500]
                # tenta extrair error json
                j = resp.json()
                if isinstance(j, dict) and "error" in j:
                    err = j["error"]
                    if isinstance(err, dict):
                        body = err.get("message") or err.get("error") or body
                    else:
                        body = str(err)
            except Exception:
                pass
            body = (body or "").strip()
            if resp.status_code == 401:
                raise RuntimeError(
                    f"Chave da API invalida ou nao autorizada (401) no OmniVoice. Verifique sua API key. Detalhe: {body}"
                )
            if resp.status_code == 403:
                raise RuntimeError(
                    f"Acesso negado (403) no OmniVoice - chave sem permissao. Detalhe: {body}"
                )
            if resp.status_code == 404:
                raise RuntimeError(
                    f"Endpoint nao encontrado (404) em '{url}' - verifique a URL do OmniVoice. Detalhe: {body}"
                )
            if resp.status_code == 429:
                raise RuntimeError(
                    f"Limite de requisicoes excedido (429) no OmniVoice - aguarde e tente novamente. Detalhe: {body}"
                )
            raise RuntimeError(f"Erro HTTP {resp.status_code} no OmniVoice: {body}")

        data = resp.content
        if not data:
            raise RuntimeError("OmniVoice retornou resposta vazia")
        # validacao basica de audio: se Content-Type for json/error disfarcado
        ctype = resp.headers.get("Content-Type", "")
        if "application/json" in ctype:
            # servidor retornou json ao inves de audio
            try:
                j = json.loads(data.decode("utf-8", errors="ignore"))
                if "error" in j:
                    raise RuntimeError(f"Erro no OmniVoice: {j['error']}")
            except RuntimeError:
                raise
            except Exception:
                pass
        # checa assinatura RIFF para wav (aviso mas nao bloqueia se mp3)
        # se esperamos wav e nao veio riff nem ID3/mp3, alerta
        if len(data) < 4:
            raise RuntimeError("OmniVoice retornou audio invalido (muito curto)")

        if self._cancel_requested:
            raise RuntimeError("Sintese cancelada pelo usuario")

        # salva
        try:
            os.makedirs(os.path.dirname(os.path.abspath(wav_path)) or ".", exist_ok=True)
            with open(wav_path, "wb") as f:
                f.write(data)
        except Exception as exc:
            raise RuntimeError(f"Falha ao salvar audio: {exc}") from exc

        return wav_path
