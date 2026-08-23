# decisions.md — Registro de Decisões e Assunções

**Branch:** feature/tts-layer
**Data:** 2026-08-22
**SDD:** specs/TTS-001.md

## Assunções até spec real da API OmniVoice
- **Default:** Adapter HTTP com flag `compat=openai|simple`
- `openai`: POST /v1/audio/speech {model, input, voice, response_format}
- `simple`: POST {text, language: pt-BR, voice}
- Mock server local valida antes de apontar para serviço real
- Quando spec real for fornecida, escalar via adapter sem retrabalho estrutural (ADR-003)

## Atalho
- **Default:** L4 segurar (padrão upstream) até usuário confirmar se prefere View+A
- Segundo L4 interrompe fala (speaker.stop)

## Jogos de teste (default até usuário definir 2 jogos)
- EN: Stardew Valley ou jogo com diálogo em inglês (placeholder)
- PT: Hades ou jogo com PT-BR (placeholder)
- Validação final exige 2 jogos reais (1 PT, 1 EN) conforme DoD

## Hardware
- Alvo: LCD e OLED, SteamOS 3.5+
- Se apenas um Deck disponível no momento da validação, registrar limitação no relatório

## Offline vs Online
- Padrão: 100% offline (Piper)
- Usuário opta por online e fornece URL + API Key; validação mostra erro amigável se key vazia

## Licença
- GPL-3.0 mantida, créditos upstream preservados

## Próximos passos
- Usuário responder spec real OmniVoice -> atualizar py_modules/providers/tts/omnivoice_provider.py e docs/decisions.md
