# ADR-003: Abstração TTSProvider + Adapter HTTP para OmniVoice

**Status:** Aceito
**Data:** 2026-08-22
**Decisor:** andre-bom + Hermes Agent
**Relacionado:** SDD specs/TTS-001.md

## Contexto
Precisamos suportar 3 provedores (Piper offline, Edge TTS online, OmniVoice API custom) com interface única. OmniVoice ainda sem spec confirmada, mas usuário fornecerá URL + API Key.

## Decisão
Criar `TTSProvider` ABC com `synthesize(text, wav_path) -> wav_path`, `cancel()`, `is_available()`. Implementar `OmniVoiceProvider` como Adapter HTTP com flag `compat`:
- `openai`: POST /v1/audio/speech {model, input, voice, response_format: wav}
- `simple`: POST {text, language: pt-BR, voice} na URL base
Headers: Authorization: Bearer {api_key}. Criar mock server local que retorna WAV 1s para validar antes da API real.

## Consequências
- Positivas: desacoplamento, fácil adicionar novos provedores, tolera spec diferente via flag.
- Negativas: Adapter precisa manter 2 formatos.

## Validação
- Mock server retorna WAV 1s e plugin reproduz.
- URL inválida retorna erro amigável (toast) sem crash.
- Troca openai/simple sem reiniciar plugin.

## Alternativas consideradas
- Um provider por endpoint: descartado por duplicação.
