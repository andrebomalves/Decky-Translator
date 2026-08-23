// src/components/VoiceControls.tsx - Compact voice controls for sidebar

import { VFC, useState, useCallback, useEffect } from "react";
import { call } from "@decky/api";
import { Focusable } from "@decky/ui";
import { FaVolumeUp, FaStop } from "react-icons/fa";

export const VoiceControls: VFC = () => {
    const [speaking, setSpeaking] = useState<boolean>(false);
    const [lastStatus, setLastStatus] = useState<string>('ocioso');

    const checkStatus = useCallback(async () => {
        try {
            const result = await call<[], any>('get_tts_status');
            if (result) {
                const isSpeaking = result.speaking === true;
                setSpeaking(isSpeaking);
                setLastStatus(isSpeaking ? 'falando' : 'ocioso');
            }
        } catch (error) {
            // TTS backend may not be available
            setSpeaking(false);
            setLastStatus('ocioso');
        }
    }, []);

    useEffect(() => {
        const interval = setInterval(checkStatus, 1000);
        return () => clearInterval(interval);
    }, [checkStatus]);

    const handleSpeak = useCallback(async () => {
        try {
            if (speaking) {
                await call<[], any>('stop_tts');
                setSpeaking(false);
                setLastStatus('ocioso');
            } else {
                await call<[], any>('speak_last_translation');
                setSpeaking(true);
                setLastStatus('falando');
            }
        } catch (error) {
            console.error('[VoiceControls] Error:', error);
        }
    }, [speaking]);

    return (
        <Focusable
            style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                padding: '4px 0',
            }}
        >
            <button
                onClick={handleSpeak}
                title={speaking ? 'Parar fala' : 'Falar última tradução'}
                style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    width: '32px',
                    height: '32px',
                    borderRadius: '50%',
                    border: speaking
                        ? '2px solid #ff6b6b'
                        : '2px solid rgba(255,255,255,0.3)',
                    background: speaking
                        ? 'rgba(255,107,107,0.2)'
                        : 'rgba(255,255,255,0.1)',
                    color: speaking ? '#ff6b6b' : '#ccc',
                    cursor: 'pointer',
                    transition: 'all 0.2s',
                }}
            >
                {speaking ? <FaStop size={14} /> : <FaVolumeUp size={14} />}
            </button>

            <div style={{
                display: 'flex',
                flexDirection: 'column',
                fontSize: '10px',
                lineHeight: '1.2',
            }}>
                <span style={{
                    color: speaking ? '#ff6b6b' : '#888',
                    fontWeight: speaking ? 'bold' : 'normal',
                }}>
                    {lastStatus === 'falando' ? '🗣️ Falando' : '🔇 Ocioso'}
                </span>
            </div>
        </Focusable>
    );
};
