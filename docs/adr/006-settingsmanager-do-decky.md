# ADR-006: SettingsManager do Decky para persistência

**Status:** Aceito
**Data:** 2026-08-22
**Decisor:** andre-bom + Hermes Agent
**Relacionado:** SDD specs/TTS-001.md

## Contexto
Config precisa persistir entre reboots e updates SteamOS, sem root, e API keys não podem vazar em logs.

## Decisão
Usar `SettingsManager` do Decky (`DECKY_PLUGIN_SETTINGS_DIR/settings.json`). Todas as chaves `tts.*` e `online.*` via ele. Mascarar keys em logs com `_mask_secret`.

## Consequências
- Positivas: sobrevive a update, sem permissão especial, padrão Decky Store.
- Negativas: JSON plano, mas suficiente.

## Validação
- Config persiste após reboot (simulado por reload).
- API Key mascarada em `decky-translator.log`.
- Troca de provider sem reiniciar plugin.

## Alternativas consideradas
- localStorage React: perde no backend. Arquivo custom: duplica SettingsManager.
