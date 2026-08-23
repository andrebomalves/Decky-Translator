# validation-log.md — Log de Validação e Correção

**Branch:** feature/tts-layer
**SDD:** specs/TTS-001.md
**DoD completo:** ver TASKS.md T6 + plano aprovado

## Como usar
Cada execução do loop de validação registra aqui: `falha -> causa raiz -> correção -> evidência`.
Só marca release quando todas as validações passarem com evidência.

## Template por execução

### Execução 1 — YYYY-MM-DD
- **Executor:** (subagente / manual)
- **Resultado:** PASS / FAIL
- Falhas:
  - [ ] (ex: Piper >500ms) -> causa: modelo não cacheado -> correção: preload -> evidência: log X
- **Evidências:** (logs, prints, WAV, screenshot)

---

## Execução 1 — 2026-08-22 (baseline)
- Status: pendente (aguarda T2-T5)
- Observações: fork criado, SDD + 7 ADRs versionados, TASKS criado. Baseline build ainda não validado no Deck.

## Critérios de Aceite (resumo)
- Funcionais: painel, offline, online, Testar voz, EN->PT, PT direto, L4 interrompe, overlay
- Performance: L4->voz <=3s offline / <=2s online, Piper <=300ms
- Qualidade: voz 1.2x inteligível, tradução 4/5
- Robustez: fallback sem rede, key vazia, volume restaura
- Compat: Game Mode LCD/OLED SteamOS 3.5+, sem root
