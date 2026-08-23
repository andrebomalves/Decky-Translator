# ADR-005: Ducking via PipeWire wpctl

**Status:** Aceito
**Data:** 2026-08-22
**Decisor:** andre-bom + Hermes Agent
**Relacionado:** SDD specs/TTS-001.md

## Contexto
Áudio do jogo compete com voz TTS. Precisamos baixar jogo durante fala e restaurar depois, no SteamOS 3.x (PipeWire/WirePlumber).

## Decisão
Usar `wpctl set-volume @DEFAULT_SINK@ 25%` ao iniciar fala e restaurar volume original em `try/finally` (mesmo se crash). Quando `tts.ducking=false`, pula.

## Consequências
- Positivas: nativo SteamOS, sem libs extras, restaura garantido.
- Negativas: afeta sink global, não por-app.

## Validação
- Volume cai para 25% durante fala e restaura com diff <=1%.
- Restaura mesmo se paplay for morto (kill).
- Sem ducking, volume permanece igual.

## Alternativas consideradas
- PulseAudio pactl: legado. Per-app ducking: complexo sem PipeWire API.
