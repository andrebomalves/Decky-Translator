# ADR-004: Auto-leitura OFF por padrão

**Status:** Aceito
**Data:** 2026-08-22
**Decisor:** andre-bom + Hermes Agent
**Relacionado:** SDD specs/TTS-001.md

## Contexto
Leitura automática após cada tradução pode poluir audio e confundir criança. Precisamos decidir comportamento padrão do gatilho de voz.

## Decisão
`tts.auto_read = false` por padrão. 1 gesto (L4 segurar) = 1 leitura. Usuário ativa auto se quiser. Segundo L4 durante fala interrompe.

## Consequências
- Positivas: controle total, sem áudio inesperado.
- Negativas: usuário precisa apertar sempre.

## Validação
- Com auto_read=false, overlay aparece sem fala até L4.
- Com true, fala automática após traduzir.
- L4 durante fala interrompe em <200ms.

## Alternativas consideradas
- Auto sempre ON: descartado por acessibilidade.
