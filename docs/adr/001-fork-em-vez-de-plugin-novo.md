# ADR-001: Fork ao invés de plugin do zero

**Status:** Aceito  
**Data:** 2026-08-22  
**Decisor:** andre-bom + Hermes Agent  
**Relacionado:** SDD specs/TTS-001.md

## Contexto
Precisamos adicionar leitura em voz alta PT-BR ao Steam Deck. Decky Translator já entrega captura PipeWire, OCR offline (Chrome Screen AI 120MB / RapidOCR 75MB), tradução offline (NLLB-200 1.4GB) e online, overlay, atalho L4 e painel Decky. Alternativa seria criar plugin novo do zero.

## Decisão
Fazer **fork de `cat-in-a-box/Decky-Translator` (GPL-3.0)** na branch `feature/tts-layer` e adicionar camada TTS plugável. Manter licença GPL-3.0 e créditos upstream. Fazer merge periódico do upstream.

## Consequências
- Positivas: reuso de ~3000 linhas testadas, time-to-market 5x menor, já publicado no Plugin Store.
- Negativas: débito de merge com upstream, necessidade de manter compatibilidade com estrutura `bin/` e `py_modules/`.
- Riscos: upstream pode quebrar API Decky; mitigado fixando `decky-frontend-lib` e CI.

## Validação
- Fork builda (`pnpm i && pnpm run build`) e carrega no Decky idêntico ao upstream antes de qualquer alteração (baseline).
- `git log --oneline` mostra branch divergindo apenas com commits TTS.

## Alternativas consideradas
- Plugin novo: descartado por duplicar captura/OCR/tradução.
- PR direto no upstream: considerado como Fase futura após validar fork.
