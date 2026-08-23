// src/tabs/TabVoice.tsx - Voice/TTS settings tab

import { VFC } from "react";
import { TtsSettings } from "../components/TtsSettings";
import { VoiceControls } from "../components/VoiceControls";

export const TabVoice: VFC = () => {
    return (
        <div>
            <VoiceControls />
            <TtsSettings />
        </div>
    );
};
