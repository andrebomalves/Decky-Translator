// src/components/TtsSettings.tsx - TTS settings panel

import {
    PanelSection,
    PanelSectionRow,
    ToggleField,
    SliderField,
    TextField,
    Field,
    ButtonItem,
    Focusable
} from "@decky/ui";

import { VFC, useState, useEffect, useCallback } from "react";
import { call } from "@decky/api";
import { FaVolumeUp, FaVolumeMute } from "react-icons/fa";

export interface TtsSettings {
    tts_provider: 'piper' | 'edge' | 'omnivoice';
    tts_ptbr_voice: string;
    tts_speed: number;
    tts_volume: number;
    tts_auto_read: boolean;
    tts_ducking: boolean;
    tts_ducking_level: number;
    online_endpoint: string;
    online_api_key: string;
    online_compat: boolean;
}

const defaultTtsSettings: TtsSettings = {
    tts_provider: 'piper',
    tts_ptbr_voice: 'pt_BR-faber-medium',
    tts_speed: 1.0,
    tts_volume: 80,
    tts_auto_read: false,
    tts_ducking: false,
    tts_ducking_level: 30,
    online_endpoint: '',
    online_api_key: '',
    online_compat: true,
};

const providerOptions = [
    { label: 'Piper (offline)', data: 'piper' as const },
    { label: 'Edge TTS (online)', data: 'edge' as const },
    { label: 'OmniVoice (online)', data: 'omnivoice' as const },
];

const piperVoiceOptions = [
    { label: 'Faber Medium (pt_BR)', data: 'pt_BR-faber-medium' },
];

const edgeVoiceOptions = [
    { label: 'FranciscaNeural (pt-BR)', data: 'pt-BR-FranciscaNeural' },
    { label: 'AntonioNeural (pt-BR)', data: 'pt-BR-AntonioNeural' },
];

export const TtsSettings: VFC = () => {
    const [ttsSettings, setTtsSettings] = useState<TtsSettings>(defaultTtsSettings);
    const [testText, setTestText] = useState<string>('Teste de voz em português');
    const [testing, setTesting] = useState<boolean>(false);
    const [testResult, setTestResult] = useState<string | null>(null);
    const [loading, setLoading] = useState<boolean>(true);

    const loadSettings = useCallback(async () => {
        try {
            const result = await call<[], any>('get_tts_settings');
            if (result) {
                setTtsSettings({
                    tts_provider: result.tts_provider || 'piper',
                    tts_ptbr_voice: result.tts_ptbr_voice || 'pt_BR-faber-medium',
                    tts_speed: result.tts_speed ?? 1.0,
                    tts_volume: result.tts_volume ?? 80,
                    tts_auto_read: result.tts_auto_read ?? false,
                    tts_ducking: result.tts_ducking ?? false,
                    tts_ducking_level: result.tts_ducking_level ?? 30,
                    online_endpoint: result.online_endpoint || '',
                    online_api_key: result.online_api_key || '',
                    online_compat: result.online_compat ?? true,
                });
            }
        } catch (error) {
            console.error('[TtsSettings] Failed to load TTS settings:', error);
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        loadSettings();
    }, [loadSettings]);

    const updateSetting = useCallback(async (key: keyof TtsSettings, value: any) => {
        setTtsSettings(prev => ({ ...prev, [key]: value }));
        try {
            await call<[any], boolean>('set_tts_settings', { [key]: value });
        } catch (error) {
            console.error(`[TtsSettings] Failed to set ${key}:`, error);
        }
    }, []);

    const handleTestVoice = useCallback(async () => {
        if (!testText.trim()) return;
        setTesting(true);
        setTestResult(null);
        try {
            const result = await call<[{ text: string }], any>('test_tts_voice', { text: testText });
            if (result && result.success) {
                setTestResult('✓ Teste concluído com sucesso');
            } else {
                setTestResult(`✗ Falha: ${result?.error || 'Erro desconhecido'}`);
            }
        } catch (error) {
            setTestResult(`✗ Erro ao testar voz: ${error}`);
        } finally {
            setTesting(false);
            setTimeout(() => setTestResult(null), 3000);
        }
    }, [testText]);

    if (loading) {
        return (
            <PanelSection title="Leitura em Voz Alta">
                <PanelSectionRow>
                    <div style={{ color: '#888', padding: '8px' }}>Carregando configurações TTS...</div>
                </PanelSectionRow>
            </PanelSection>
        );
    }

    const currentVoiceOptions = ttsSettings.tts_provider === 'piper'
        ? piperVoiceOptions
        : ttsSettings.tts_provider === 'edge'
            ? edgeVoiceOptions
            : [];

    return (
        <div>
            <PanelSection title="Leitura em Voz Alta">
                {/* Provider Toggle */}
                <PanelSectionRow>
                    <Field label="Provedor de Voz">
                        <Focusable style={{ display: 'flex', gap: '4px', marginTop: '4px' }}>
                            {providerOptions.map(opt => (
                                <button
                                    key={opt.data}
                                    onClick={() => updateSetting('tts_provider', opt.data)}
                                    style={{
                                        flex: 1,
                                        padding: '8px 4px',
                                        border: ttsSettings.tts_provider === opt.data
                                            ? '2px solid #1a9fff'
                                            : '1px solid rgba(255,255,255,0.2)',
                                        borderRadius: '6px',
                                        background: ttsSettings.tts_provider === opt.data
                                            ? 'rgba(26,159,255,0.2)'
                                            : 'rgba(255,255,255,0.05)',
                                        color: ttsSettings.tts_provider === opt.data
                                            ? '#fff'
                                            : '#aaa',
                                        cursor: 'pointer',
                                        fontSize: '12px',
                                        fontWeight: ttsSettings.tts_provider === opt.data
                                            ? 'bold'
                                            : 'normal',
                                        transition: 'all 0.2s',
                                    }}
                                >
                                    {opt.label}
                                </button>
                            ))}
                        </Focusable>
                    </Field>
                </PanelSectionRow>

                {/* Voice Selection */}
                <PanelSectionRow>
                    {ttsSettings.tts_provider === 'omnivoice' ? (
                        <TextField
                            label="Nome da Voz (OmniVoice)"
                            value={ttsSettings.tts_ptbr_voice}
                            onChange={(e) => updateSetting('tts_ptbr_voice', e.target.value)}
                            placeholder="Ex: pt-br-faber"
                        />
                    ) : (
                        <Field label="Voz">
                            <Focusable style={{ display: 'flex', flexDirection: 'column', gap: '4px', marginTop: '4px' }}>
                                {currentVoiceOptions.map(opt => (
                                    <button
                                        key={opt.data}
                                        onClick={() => updateSetting('tts_ptbr_voice', opt.data)}
                                        style={{
                                            padding: '8px 12px',
                                            border: ttsSettings.tts_ptbr_voice === opt.data
                                                ? '2px solid #1a9fff'
                                                : '1px solid rgba(255,255,255,0.2)',
                                            borderRadius: '6px',
                                            background: ttsSettings.tts_ptbr_voice === opt.data
                                                ? 'rgba(26,159,255,0.2)'
                                                : 'rgba(255,255,255,0.05)',
                                            color: ttsSettings.tts_ptbr_voice === opt.data
                                                ? '#fff'
                                                : '#aaa',
                                            cursor: 'pointer',
                                            fontSize: '12px',
                                            textAlign: 'left',
                                            transition: 'all 0.2s',
                                        }}
                                    >
                                        {opt.label}
                                    </button>
                                ))}
                            </Focusable>
                        </Field>
                    )}
                </PanelSectionRow>

                {/* Speed Slider */}
                <PanelSectionRow>
                    <SliderField
                        value={ttsSettings.tts_speed}
                        min={0.5}
                        max={2.0}
                        step={0.1}
                        label="Velocidade"
                        description="1.0=normal, 1.2 recomendado"
                        showValue={true}
                        valueSuffix="x"
                        onChange={(value) => updateSetting('tts_speed', Math.round(value * 10) / 10)}
                    />
                </PanelSectionRow>

                {/* Volume Slider */}
                <PanelSectionRow>
                    <SliderField
                        value={ttsSettings.tts_volume}
                        min={0}
                        max={100}
                        step={1}
                        label="Volume"
                        showValue={true}
                        valueSuffix="%"
                        onChange={(value) => updateSetting('tts_volume', Math.round(value))}
                    />
                </PanelSectionRow>

                {/* Ducking Toggle */}
                <PanelSectionRow>
                    <ToggleField
                        checked={ttsSettings.tts_ducking}
                        label="Reduzir volume do jogo"
                        description="Baixa o volume do jogo enquanto fala"
                        onChange={(value) => updateSetting('tts_ducking', value)}
                    />
                </PanelSectionRow>

                {/* Ducking Level - only when ducking is enabled */}
                {ttsSettings.tts_ducking && (
                    <PanelSectionRow>
                        <SliderField
                            value={ttsSettings.tts_ducking_level}
                            min={0}
                            max={100}
                            step={1}
                            label="Nível de Redução"
                            description="Quanto reduzir o volume do jogo"
                            showValue={true}
                            valueSuffix="%"
                            onChange={(value) => updateSetting('tts_ducking_level', Math.round(value))}
                        />
                    </PanelSectionRow>
                )}

                {/* Auto Read Toggle */}
                <PanelSectionRow>
                    <ToggleField
                        checked={ttsSettings.tts_auto_read}
                        label="Ler automaticamente"
                        description="Lê o texto traduzido automaticamente"
                        onChange={(value) => updateSetting('tts_auto_read', value)}
                    />
                </PanelSectionRow>
            </PanelSection>

            {/* OmniVoice-specific settings */}
            {ttsSettings.tts_provider === 'omnivoice' && (
                <PanelSection title="OmniVoice - Configurações Online">
                    <PanelSectionRow>
                        <TextField
                            label="Endpoint"
                            value={ttsSettings.online_endpoint}
                            onChange={(e) => updateSetting('online_endpoint', e.target.value)}
                            placeholder="https://api.example.com/tts"
                        />
                    </PanelSectionRow>
                    <PanelSectionRow>
                        <TextField
                            label="API Key"
                            value={ttsSettings.online_api_key}
                            onChange={(e) => updateSetting('online_api_key', e.target.value)}
                            placeholder="sk-..."
                        />
                    </PanelSectionRow>
                    <PanelSectionRow>
                        <ToggleField
                            checked={ttsSettings.online_compat}
                            label="Compatibilidade"
                            description="Modo compatível com APIs OpenAI"
                            onChange={(value) => updateSetting('online_compat', value)}
                        />
                    </PanelSectionRow>
                </PanelSection>
            )}

            {/* Test Voice Section */}
            <PanelSection title="Testar Voz">
                <PanelSectionRow>
                    <TextField
                        label="Texto para teste"
                        value={testText}
                        onChange={(e) => setTestText(e.target.value)}
                        placeholder="Digite o texto para testar a voz"
                    />
                </PanelSectionRow>
                <PanelSectionRow>
                    <ButtonItem
                        layout="below"
                        onClick={handleTestVoice}
                        disabled={testing || !testText.trim()}
                    >
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                            {testing ? (
                                <FaVolumeMute style={{ color: '#888' }} />
                            ) : (
                                <FaVolumeUp style={{ color: '#1a9fff' }} />
                            )}
                            {testing ? 'Testando...' : 'Testar voz'}
                        </div>
                    </ButtonItem>
                </PanelSectionRow>
                {testResult && (
                    <PanelSectionRow>
                        <div style={{
                            padding: '8px 12px',
                            borderRadius: '6px',
                            fontSize: '12px',
                            background: testResult.startsWith('✓')
                                ? 'rgba(40, 167, 69, 0.2)'
                                : 'rgba(220, 53, 69, 0.2)',
                            color: testResult.startsWith('✓') ? '#28a745' : '#dc3545',
                        }}>
                            {testResult}
                        </div>
                    </PanelSectionRow>
                )}
            </PanelSection>
        </div>
    );
};
