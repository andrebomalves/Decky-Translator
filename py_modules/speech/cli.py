"""speech.cli — CLI standalone para teste de TTS sem Decky.

Uso:
    python -m speech.cli "Olá mundo!"
    python -m speech.cli --text "Teste" --provider edge --output /tmp/test.wav
"""
from __future__ import annotations

import argparse
import logging
import os
import sys
import tempfile

# Garante que py_modules está no path
_MODULE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _MODULE_DIR not in sys.path:
    sys.path.insert(0, _MODULE_DIR)

from speech.speaker import Speaker, Priority


def _get_provider(name: str, **kwargs):
    """Retorna instância do provider pelo nome."""
    name = name.lower().strip()

    if name == "piper":
        from providers.tts.piper_provider import PiperTTSProvider
        return PiperTTSProvider(**kwargs)
    elif name == "edge":
        from providers.tts.edge_provider import EdgeTTSProvider
        return EdgeTTSProvider(**kwargs)
    elif name == "omnivoice":
        from providers.tts.omnivoice_provider import OmniVoiceProvider
        return OmniVoiceProvider(**kwargs)
    else:
        raise ValueError(f"Provider desconhecido: {name}. Opções: piper, edge, omnivoice")


def main():
    parser = argparse.ArgumentParser(
        description="Teste standalone de TTS (sem Decky)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Exemplos:\n"
               '  python -m speech.cli "Olá mundo!"\n'
               '  python -m speech.cli --text "Teste" --provider edge\n'
               '  python -m speech.cli --text "Teste" --no-ducking --output /tmp/test.wav\n',
    )
    parser.add_argument("text", nargs="?", default=None, help="Texto para sintetizar")
    parser.add_argument("--text", "-t", dest="text_flag", default=None, help="Texto (alternativa)")
    parser.add_argument("--provider", "-p", default="piper", choices=["piper", "edge", "omnivoice"],
                        help="Provider TTS (default: piper)")
    parser.add_argument("--no-ducking", action="store_true", help="Desabilitar ducking de volume")
    parser.add_argument("--output", "-o", default=None, help="Caminho do WAV de saída")
    parser.add_argument("--speed", "-s", type=float, default=1.0, help="Velocidade (1.0 = normal)")
    parser.add_argument("--priority", type=int, default=Priority.NORMAL, choices=range(0, 4),
                        help="Prioridade (0=urgente, 3=baixa)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Logging detalhado")
    parser.add_argument("--no-play", action="store_true", help="Apenas sintetizar, não reproduzir")

    args = parser.parse_args()

    # Configura logging
    level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )
    logger = logging.getLogger("speech.cli")

    # Resolve texto
    text = args.text_flag or args.text
    if not text:
        parser.error("Forneça o texto como argumento posicional ou via --text")

    # Resolve output path
    if args.output:
        wav_path = args.output
    else:
        wav_path = os.path.join(tempfile.gettempdir(), "decky_tts_cli_output.wav")

    logger.info(f"Provider: {args.provider}")
    logger.info(f"Texto: {text[:80]}{'...' if len(text) > 80 else ''}")
    logger.info(f"Saída: {wav_path}")

    # Cria provider
    provider = _get_provider(args.provider, speed=args.speed)

    if not provider.is_available():
        logger.error(
            f"Provider '{args.provider}' não está disponível. "
            f"Verifique se o modelo/dependências estão instalados."
        )
        sys.exit(1)

    # Sintetiza
    logger.info("Sintetizando...")
    try:
        result_path = provider.synthesize(text, wav_path)
        logger.info(f"Síntese concluída: {result_path}")

        # Mostra info do arquivo WAV
        import wave
        with wave.open(result_path, "rb") as wf:
            frames = wf.getnframes()
            rate = wf.getframerate()
            duration = frames / rate
            logger.info(f"  Canais: {wf.getnchannels()}, Sample rate: {rate}Hz, Duração: {duration:.2f}s")

    except Exception as exc:
        logger.error(f"Falha na síntese: {exc}")
        sys.exit(1)

    # Reproduz
    if not args.no_play:
        duck_cfg = {"enabled": not args.no_ducking, "level_percent": 25}
        speaker = Speaker()
        speaker.start()

        done_event = __import__("threading").Event()
        speaker.speak(
            text=text,
            wav_path=result_path,
            provider=None,  # já sintetizado
            ducking_config=duck_cfg,
            on_done_callback=lambda: done_event.set(),
            priority=args.priority,
        )

        logger.info("Reproduzindo...")
        done_event.wait(timeout=30)
        speaker.stop()
        logger.info("Concluído!")
    else:
        logger.info("Arquivo salvo (reprodução desabilitada com --no-play)")


if __name__ == "__main__":
    main()
