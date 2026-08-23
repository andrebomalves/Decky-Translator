# validation-log.md — Log de Validação e Correção

**Branch:** feature/tts-layer
**SDD:** specs/TTS-001.md
**DoD completo:** ver TASKS.md T6 + plano aprovado

---

## Execução 2 — 2026-08-23
- **Executor:** Hermes Agent (revisão + correções + implementação completa TTS)
- **Resultado:** COMPLETO — pipeline TTS integrado, zip gerado, validação Deck pendente

### Revisão encontrou e corrigiu (contrato RPC frontend <-> backend)
1. `get_tts_settings` / `set_tts_settings` não existiam no backend → implementados
2. `stop_tts` / `speak_last_translation` não existiam → implementados com Speaker real
3. `online_compat` era boolean no frontend vs enum string no SDD → corrigido para `openai`/`simple`
4. `test_tts_voice` retornava `ok` mas frontend lia `success` → corrigido
5. `get_tts_status` não retornava `speaking` → adicionado via TTSManager
6. Defaults divergentes (ducking false/30 no frontend vs true/25 no SDD) → alinhados
7. `get_all_settings` vazava `online_api_key` crua → mascarada (ADR-006)
8. Bug `load_api_key(...) if False else ...` em `_main` → removido

### Implementações novas
| Item | Status |
|---|---|
| `py_modules/speech/manager.py` — TTSManager (orquestração) | ✅ |
| `py_modules/providers/tts/piper_downloader.py` — modelo sob demanda com progresso/resume (ADR-007) | ✅ |
| Botão "Instalar voz offline (~50MB)" no painel + `download_piper_model`/`get_piper_model_status` | ✅ |
| `speak_last_translation` manual + auto_read no pipeline de tradução (ADR-004) | ✅ |
| Interrupção por segundo L4 durante fala (`interruptTtsIfSpeaking`) | ✅ |
| Edge TTS: MP3 salvo com extensão correta + `ffplay` fallback no Speaker | ✅ |
| Speaker: `shutil.which` para detecção de player, player dedicado para MP3 | ✅ |

### Validações executadas
- [x] Python syntax: todos os `.py` compilam
- [x] TypeScript build: `npm run build` passa (warnings pré-existentes do upstream)
- [x] Mock OmniVoice: `compat=openai` e `compat=simple` retornam WAV 22050Hz válido
- [x] 401 com key errada → erro amigável PT-BR
- [x] TTSManager: set_settings persiste, test_voice sem modelo retorna erro amigável
- [x] Zip gerado: `Decky-Voice-Reader-0.9.1.zip` (1.8MB) com main.py, dist/, py_modules/, docs/

### Validações pendentes (requer Steam Deck)
- [ ] Plugin carrega no Decky Loader (Developer → Install from ZIP)
- [ ] Piper offline: baixar modelo, testar voz audível
- [ ] Pipeline completo: L4 → captura → OCR → tradução → TTS → fala
- [ ] Ducking: volume cai durante fala, restaura depois
- [ ] Interrupção: L4 durante fala cancela
- [ ] Performance: L4→voz ≤3s offline

## Execução 1 — 2026-08-23
- **Executor:** Hermes Agent (4+2 subagentes em paralelo)
- **Resultado:** PARCIAL — implementação completa, validação Deck pendente

### Arquivos criados (15 novos)
| Arquivo | Tamanho | Status |
|---|---|---|
| `py_modules/providers/tts/base.py` | 653B | ✅ syntax OK |
| `py_modules/providers/tts/piper_provider.py` | 11223B | ✅ syntax OK |
| `py_modules/providers/tts/edge_provider.py` | 4999B | ✅ syntax OK |
| `py_modules/providers/tts/omnivoice_provider.py` | 9024B | ✅ syntax OK |
| `py_modules/speech/normalizer.py` | 1424B | ✅ syntax OK |
| `py_modules/speech/chunker.py` | 3048B | ✅ syntax OK |
| `py_modules/speech/ducking.py` | 3176B | ✅ syntax OK |
| `py_modules/speech/speaker.py` | 9752B | ✅ syntax OK |
| `py_modules/speech/cli.py` | 5032B | ✅ syntax OK |
| `py_modules/speech/__main__.py` | 109B | ✅ syntax OK |
| `test/mock_omnivoice.py` | 5614B | ✅ syntax OK |
| `src/components/TtsSettings.tsx` | 15331B | ✅ build OK |
| `src/components/VoiceControls.tsx` | 3282B | ✅ build OK |
| `src/tabs/TabVoice.tsx` | 346B | ✅ build OK |
| `requirements.txt` | 351B | ✅ atualizado |

### Arquivos modificados
| Arquivo | Mudanças | Status |
|---|---|---|
| `main.py` | +140 linhas (settings, test_tts_voice, get_tts_status) | ✅ |
| `src/index.tsx` | +TabVoice, +IconVoice | ✅ |
| `src/tabs/index.ts` | +TabVoice export | ✅ |

### Validações executadas
- [x] Python syntax: 11/11 `.py` compilan sem erro
- [x] TypeScript build: `npm run build` passa (5.6s, warnings pré-existentes)
- [x] Git: 4 commits, push OK para `andrebomalves/Decky-Translator:feature/tts-layer`
- [x] Bug indentação main.py corrigido (logger.error)

### Validações pendentes (requer Steam Deck)
- [ ] Plugin carrega no Decky Loader
- [ ] Painel "Leitura em Voz Alta" aparece na aba Voice
- [ ] Piper offline: `test_tts_voice` sintetiza WAV audível
- [ ] Edge TTS online: conecta e sintetiza
- [ ] OmniVoice mock: POST retorna WAV, adapter funciona
- [ ] Pipeline completo: L4 → captura → OCR → tradução → TTS → fala
- [ ] Ducking: volume cai durante fala, restaura depois
- [ ] Interrupção: L4 durante fala cancela
- [ ] Performance: L4→voz ≤3s offline

### Correções aplicadas
1. **main.py indentação** — `logger.error` estava na coluna 0 dentro de `except`, corrigido para 12 espaços

### Próximos passos
1. Instalar no Steam Deck via Decky Loader (Developer → Install from ZIP)
2. Rodar `python -m speech.cli "Olá, vamos jogar?"` para validar Piper
3. Testar mock server: `python test/mock_omnivoice.py` + configurar OmniVoice no painel
4. Testar em 2 jogos reais (1 PT, 1 EN)
5. Validar todos os critérios DoD e registrar aqui
