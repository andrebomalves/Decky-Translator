"""speech.normalizer — limpatexto OCR para TTS PT-BR."""
import re

_ZERO_WIDTH_RE = re.compile(r"[\u200b\u200c\u200d\u2060\ufeff\xad]")
_MULTI_SPACE_RE = re.compile(r"[ \t]+")
_MULTI_NEWLINE_RE = re.compile(r"\n{3,}")
# caracteres comuns de ruído OCR que aparecem isolados
_NOISE_CHARS = set("|¦¬°·•�")

def normalize(text: str) -> str:
    """Limpa quebras, ruído e espaços do OCR. Retorna string vazia se nada útil."""
    if not text or not isinstance(text, str):
        return ""
    # remove zero-width / soft hyphen
    text = _ZERO_WIDTH_RE.sub("", text)
    # remove ruído isolado tipo "|" solto
    # mantemos pontuação válida
    lines = []
    for line in text.splitlines():
        stripped = line.strip()
        # ignora linha que é só ruído/pontuação decorativa
        if not stripped:
            continue
        if len(stripped) <= 2 and all(c in _NOISE_CHARS or c in " -_=*~`" for c in stripped):
            continue
        lines.append(stripped)
    text = " ".join(lines)
    # colapsa espaços
    text = _MULTI_SPACE_RE.sub(" ", text)
    # remove espaços antes de pontuação
    text = re.sub(r"\s+([,.!?;:])", r"\1", text)
    # normaliza quebras remanescentes
    text = text.strip()
    return text


# alias esperado por algumas specs
def normalize_text(text: str) -> str:
    return normalize(text)

def clean_ocr_text(text: str) -> str:
    return normalize(text)
