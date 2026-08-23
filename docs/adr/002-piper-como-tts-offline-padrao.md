# ADR-002: Piper como TTS offline padrão

**Status:** Aceito
**Data:** 2026-08-22
**Decisor:** andre-bom + Hermes Agent
**Relacionado:** SDD specs/TTS-001.md

## Contexto
Precisamos de TTS 100% offline em PT-BR que rode no CPU Zen2 do Steam Deck sem GPU, com latência baixa e tamanho pequeno. Opções: Piper (ONNX, ~50MB), Mimic3, Coqui, eSpeak.

## Decisão
Usar **Piper `pt_BR-faber-medium`** como provedor padrão offline. ~50MB, ~50ms por frase, CPU-only, ONNX Runtime já presente para OCR. Velocidade padrão 1.0, recomendado 1.2 para crianças (length_scale).

## Consequências
- Positivas: offline total, latência <300ms, qualidade inteligível, sem dependência de nuvem.
- Negativas: qualidade inferior a neural cloud; modelo precisa ser baixado sob demanda.
- Mitigação: fallback Edge TTS / OmniVoice quando online.

## Validação
- Frase "Olá! Vamos jogar?" sintetiza <500ms em modo avião.
- 3 ouvintes confirmam inteligibilidade em 1.2x.
- Arquivo WAV gerado é PCM 22050Hz válido (ffprobe).

## Alternativas consideradas
- Mimic3: maior, mais lento. Coqui: pesado. eSpeak: robótico.
