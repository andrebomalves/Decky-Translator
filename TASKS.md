# TASKS — Decky Voice Reader (Fork Decky-Translator + TTS)

> Branch: `feature/tts-layer` | SDD: `specs/TTS-001.md` | ADRs: `docs/adr/`

## F0 — Preparação
- [ ] T0.1 Fork + branch + pastas (FEITO: specs/TTS-001.md, adr/001)
- [x] T0.2 Validar baseline build (`pnpm i && pnpm run build`)
- [ ] T0.3 Criar ADRs 002-007 + TASKS + decisions + validation-log

## F1 — Baseline
- [ ] T1.1 Buildar fork puro e validar carga no Decky (sem alterações TTS)

## F2 — TTS Core (offline)
- [ ] T2.1 `py_modules/providers/tts/base.py` — TTSProvider ABC
- [ ] T2.2 `py_modules/speech/normalizer.py` + `chunker.py`
- [ ] T2.3 `py_modules/providers/tts/piper_provider.py` — Piper pt_BR-faber-medium
- [ ] T2.4 `py_modules/speech/speaker.py` + `ducking.py` (wpctl)
- [ ] T2.5 `py_modules/speech/cli.py` — teste CLI `python -m speech.cli "Olá, vamos jogar?"`
- [ ] T2.6 Mock WAV + teste paplay sem Deck

## F3 — Provedores Online
- [ ] T3.1 `py_modules/providers/tts/edge_provider.py`
- [ ] T3.2 `py_modules/providers/tts/omnivoice_provider.py` (compat openai/simple)
- [ ] T3.3 `test/mock_omnivoice.py` — servidor mock retorna WAV 1s
- [ ] T3.4 Testes: URL inválida -> erro amigável, key vazia bloqueia

## F4 — Painel Frontend
- [ ] T4.1 `src/components/TtsSettings.tsx` — seção TTS (provider, voz, sliders)
- [ ] T4.2 `src/components/VoiceControls.tsx` — Testar voz, volume, velocidade
- [ ] T4.3 Persistência via SettingsManager (tts.*, online.*)
- [ ] T4.4 Integração em `src/tabs/` e `src/index.tsx`

## F5 — Integração Fluxo
- [ ] T5.1 Hook pós-OCR em `main.py`: langdetect -> [EN? traduz] -> normalizer -> chunker -> speaker.speak()
- [ ] T5.2 Debounce (texto==ultimo -> ignora) + interrupção L4 (speaker.stop())
- [ ] T5.3 Chunking texto longo sem cortar palavra

## F6 — Validação Loop (DoD)
- [ ] T6.1 Funcionais: painel aparece, offline sem rede, online com URL+Key, Testar voz, EN->PT, PT direto, L4 interrompe, overlay intacto
- [ ] T6.2 Performance: L4->voz <=3s offline / <=2s online, Piper <=300ms, CPU <30% 1 core
- [ ] T6.3 Qualidade: voz 1.2x inteligível, tradução 4/5
- [ ] T6.4 Robustez: sem rede + fallback, key vazia, volume sempre restaura
- [ ] T6.5 Compat: Game Mode LCD/OLED, sem root, key mascarada
- [ ] T6.6 Loop correção: falha -> causa raiz -> correção -> re-valida até 100% (log em docs/validation-log.md)

## Ordem
T0 -> T1 -> T2 -> T3 -> T4 -> T5 -> T6 (sequencial, cada fase só avança com aceite verificável)

## Evidência por Task
Cada task exige output verificável (log, print, WAV, screenshot) antes de marcar como concluída.
