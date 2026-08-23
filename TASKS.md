# TASKS — Decky Voice Reader (Fork Decky-Translator + TTS)

> Branch: `feature/tts-layer` | SDD: `specs/TTS-001.md` | ADRs: `docs/adr/`
> Repo: https://github.com/andrebomalves/Decky-Translator/tree/feature/tts-layer

## F0 — Preparação ✅
- [x] T0.1 Fork + branch `feature/tts-layer` + pastas specs/docs/py_modules
- [x] T0.2 Validar baseline build (`npm run build` passa)
- [x] T0.3 Criar SDD TTS-001 + 7 ADRs + TASKS + decisions + validation-log

## F1 — Baseline ✅
- [x] T1.1 Fork builda e carrega idêntico ao upstream (commit `4358712`)

## F2 — TTS Core (offline) ✅
- [x] T2.1 `py_modules/providers/tts/base.py` — TTSProvider ABC (653B)
- [x] T2.2 `py_modules/speech/normalizer.py` + `chunker.py` (1424B + 3048B)
- [x] T2.3 `py_modules/providers/tts/piper_provider.py` — Piper pt_BR-faber-medium (11223B)
- [x] T2.4 `py_modules/speech/speaker.py` + `ducking.py` (9752B + 3176B)
- [x] T2.5 `py_modules/speech/cli.py` + `__main__.py` — teste CLI (5032B + 109B)
- [x] T2.6 `test/mock_omnivoice.py` — servidor mock WAV 440Hz (5614B)

## F3 — Provedores Online ✅
- [x] T3.1 `py_modules/providers/tts/edge_provider.py` (4999B)
- [x] T3.2 `py_modules/providers/tts/omnivoice_provider.py` — adapter openai/simple (9024B)
- [x] T3.3 `test/mock_omnivoice.py` — POST /v1/audio/speech → WAV 1s (T2.6)
- [x] T3.4 Validação: URL inválida → erro PT-BR, key vazia → bloqueia

## F4 — Painel Frontend ✅
- [x] T4.1 `src/components/TtsSettings.tsx` — provider toggle, voices, sliders, ducking (15331B)
- [x] T4.2 `src/components/VoiceControls.tsx` — play/stop, status (3282B)
- [x] T4.3 `src/tabs/TabVoice.tsx` — aba dedicada voz (346B)
- [x] T4.4 Integração `src/index.tsx` + `src/tabs/index.ts` (4th tab)

## F5 — Integração Fluxo ✅
- [x] T5.1 main.py: settings TTS (tts_provider/volume/speed/ducking/etc) + load/save
- [x] T5.2 main.py: test_tts_voice (valida provider, endpoint, key, retorna status)
- [x] T5.3 main.py: get_tts_status (expõe estado completo ao frontend)
- [x] T5.4 main.py: SENSITIVE_SETTING_KEYS inclui online_api_key
- [x] T5.5 main.py: bug indentação corrigido (logger.error)

## F6 — Validação Loop
- [x] T6.1 Python syntax: 11/11 arquivos `.py` compilan sem erro ✅
- [x] T6.2 TypeScript build: `npm run build` passa (5.6s) ✅
- [x] T6.3 Git: 4 commits limpos, push OK ✅
- [x] T6.8 Revisão contrato RPC frontend/backend — corrigidos get/set_tts_settings, stop_tts, speak_last_translation, online_compat enum, ok vs success, speaking status ✅
- [x] T6.9 Implementação completa TTS: TTSManager, PiperDownloader, auto_read, interrupção L4, Edge MP3/ffplay, zip gerado ✅

### Validação pendente (requer Steam Deck real)
- [ ] T6.4 Funcionais no Deck: painel aparece, offline funciona, Testar voz toca
- [ ] T6.5 Performance: L4→voz ≤3s offline, Piper ≤300ms
- [ ] T6.6 Jogos reais: 1 PT + 1 EN, pipeline completo
- [ ] T6.7 Acessibilidade: uso só L4, feedback <200ms

## Commits
```
44409ed feat(tts-core): pipeline completo offline/online + settings + provider base
e65e3a0 feat(tts-core): piper + speaker + cli + mock server
2dd6055 feat(frontend): painel TTS com controles de voz
86d6fe7 docs: SDD TTS-001 + 7 ADRs + TASKS + decisions + validation-log
```
