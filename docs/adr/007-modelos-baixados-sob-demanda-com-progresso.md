# ADR-007: Modelos baixados sob demanda com progresso e resume

**Status:** Aceito
**Data:** 2026-08-22
**Decisor:** andre-bom + Hermes Agent
**Relacionado:** SDD specs/TTS-001.md

## Contexto
Modelos (Piper 50MB, NLLB 1.4GB, RapidOCR 75MB) não podem inflar zip do plugin (limite Store). Precisam estar disponíveis offline após primeiro download.

## Decisão
Download sob demanda com indicador de progresso, resume parcial e verificação SHA256. Botão "Instalar dependências" no painel. Pasta `defaults/models/` e `bin/`. Se interrompido, retoma.

## Consequências
- Positivas: zip leve, usuário escolhe o que baixar, resume economiza dados.
- Negativas: primeiro uso precisa rede.

## Validação
- Interromper download no meio e retomar completa sem corrupção.
- SHA256 detecta arquivo corrompido e re-baixa.
- Offline após download: funciona em modo avião.

## Alternativas consideradas
- Bundlar tudo no zip: rejeitado por limite Store e tamanho.
