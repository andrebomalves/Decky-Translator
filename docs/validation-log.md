# validation-log.md — Log de Validação e Correção

**Branch:** feature/tts-layer
**SDD:** specs/TTS-001.md
**DoD completo:** ver TASKS.md T6 + plano aprovado

---

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
