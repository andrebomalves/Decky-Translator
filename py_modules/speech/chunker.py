"""Chunker: quebra texto em blocos <= max_chars sem cortar palavra."""
from __future__ import annotations

import re
from typing import Iterator, List

_SENTENCE_END = re.compile(r'[.!?;:。！？]\s+')
_PARA_RE = re.compile(r'\n\n+')


def chunk(text: str, max_chars: int = 400) -> List[str]:
    """Quebra texto em chunks <= max_chars sem cortar palavra.

    Ordem de preferencia para split:
    1. quebra de paragrafo (\\n\\n)
    2. pontuacao de frase (.!?;:)
    3. ultimo espaco
    4. hard split (palavra/URL longa)
    """
    if not text:
        return []
    text = text.strip()
    if not text:
        return []
    if len(text) <= max_chars:
        return [text]

    chunks: List[str] = []
    remaining = text

    while remaining:
        remaining = remaining.lstrip(' \n"\'-–—\t')
        if not remaining:
            break
        if len(remaining) <= max_chars:
            c = remaining.strip()
            if c:
                # ajuda prosodia Piper se termina sem pontuacao
                if c[-1] not in '.!?:;。！？…':
                    c += '.'
                chunks.append(c)
            break

        window = remaining[:max_chars]

        # 1) paragrafo dentro da janela
        para_idx = window.rfind('\n\n')
        if para_idx > 0 and para_idx >= max_chars * 0.3:
            split_at = para_idx + 2
            c = remaining[:split_at].strip()
            if c:
                chunks.append(c)
            remaining = remaining[split_at:]
            continue

        # 2) pontuacao de frase
        # procura ultima pontuacao seguida de espaco dentro da janela
        last_punct = -1
        for m in re.finditer(r'[.!?;:。！？]\s', window):
            last_punct = m.end()  # inclui espaco
        # tambem considera pontuacao no limite sem espaco (ex: "ola. proximo")
        if last_punct == -1:
            for m in re.finditer(r'[.!?;:。！？]', window):
                # so usa se nao for muito no comeco
                if m.end() >= max_chars * 0.4:
                    last_punct = m.end()
        if last_punct > 0 and last_punct >= max_chars * 0.4:
            # trim para nao deixar espaco final
            c = remaining[:last_punct].strip()
            if c:
                chunks.append(c)
            remaining = remaining[last_punct:]
            continue

        # 3) ultimo espaco
        space_idx = window.rfind(' ')
        if space_idx > 0 and space_idx >= max_chars * 0.5:
            c = remaining[:space_idx].strip()
            if c:
                chunks.append(c)
            remaining = remaining[space_idx:]
            continue

        # 4) hard split
        c = remaining[:max_chars].strip()
        if c:
            chunks.append(c)
        remaining = remaining[max_chars:]

    # remove vazios e garante trim
    chunks = [c.strip() for c in chunks if c.strip()]
    return chunks


def chunk_iter(text: str, max_chars: int = 400) -> Iterator[str]:
    """Generator wrapper."""
    for c in chunk(text, max_chars=max_chars):
        yield c
