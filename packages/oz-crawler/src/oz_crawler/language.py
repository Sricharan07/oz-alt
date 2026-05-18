from __future__ import annotations

import re


ENGLISH_MARKERS = {
    "the",
    "and",
    "for",
    "with",
    "from",
    "this",
    "that",
    "use",
    "using",
    "return",
    "returns",
    "example",
    "install",
    "configure",
    "request",
    "response",
}

NON_ENGLISH_MARKERS = {
    "es": {"el", "la", "los", "las", "para", "con", "desde", "ejemplo", "configurar"},
    "fr": {"le", "la", "les", "pour", "avec", "depuis", "exemple", "configurer"},
    "de": {"der", "die", "das", "und", "mit", "fur", "beispiel", "konfigurieren"},
    "pt": {"para", "com", "exemplo", "configurar", "resposta", "requisicao"},
    "it": {"per", "con", "esempio", "configurare", "risposta", "richiesta"},
}


def language_allowed(text: str, target_language: str = "en") -> bool:
    target = (target_language or "en").strip().lower()
    if target in {"", "*", "any", "all"}:
        return True
    if code_density(text) > 0.45:
        return True
    detected = detect_language(text)
    if detected == "unknown":
        return True
    return detected == target


def detect_language(text: str) -> str:
    normalized = normalize_text(text)
    if not normalized:
        return "unknown"
    try:
        from langdetect import detect  # type: ignore

        return str(detect(normalized[:4000])).lower()
    except Exception:
        return heuristic_language(normalized)


def heuristic_language(text: str) -> str:
    words = re.findall(r"[a-zA-ZÀ-ÿ]{2,}", text.lower())
    if len(words) < 40:
        return "unknown"
    total = len(words)
    english_score = sum(1 for word in words if word in ENGLISH_MARKERS) / total
    if english_score >= 0.035:
        return "en"
    scores = {
        language: sum(1 for word in words if strip_accents(word) in markers) / total
        for language, markers in NON_ENGLISH_MARKERS.items()
    }
    language, score = max(scores.items(), key=lambda item: item[1])
    return language if score >= 0.035 else "unknown"


def normalize_text(text: str) -> str:
    text = re.sub(r"```.*?```", " ", text, flags=re.S)
    text = re.sub(r"`[^`]+`", " ", text)
    text = re.sub(r"https?://\S+", " ", text)
    return text


def code_density(text: str) -> float:
    if not text.strip():
        return 0.0
    code_markers = len(re.findall(r"```|\b(function|class|const|let|var|def|import|export|return)\b|[{}();=]", text))
    words = max(1, len(re.findall(r"\w+", text)))
    return min(1.0, code_markers / words)


def strip_accents(value: str) -> str:
    return (
        value.replace("é", "e")
        .replace("è", "e")
        .replace("ê", "e")
        .replace("á", "a")
        .replace("à", "a")
        .replace("í", "i")
        .replace("ó", "o")
        .replace("ú", "u")
        .replace("ç", "c")
        .replace("ñ", "n")
        .replace("ü", "u")
    )
