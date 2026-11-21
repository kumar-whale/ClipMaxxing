"""Speech to text and the caption language, chosen in the dashboard (Settings, AI, Speech and captions).

Saved in speech.json in the data folder, next to ai.json. What is saved there wins over .env:

    CLIPMAXXING_CAPTION_LANGUAGE   english (default): every caption is in English. Hindi, Urdu and every other language
                             are translated into English.
                             hinglish: English stays English, Hindi and Urdu are written in Roman letters
                             ("yaar ye kya hai"), every other language is translated into English.
    CLIPMAXXING_SPEECH             local (default): the speech model on this machine. Free, but it understands English only.
                             openai | groq: Whisper on that service, with your key. Understands about 100 languages,
                             Hindi included, so uploads in Hindi get proper English captions.
    CLIPMAXXING_SPEECH_KEY         the key for that service. Empty: the AI key is used when the AI is the same service.
    CLIPMAXXING_SPEECH_MODEL       optional: whisper-1 (OpenAI) or whisper-large-v3 (Groq) by default.

Whisper is sent the sound only (16 kHz mono), in pieces of up to 10 minutes. If it fails, the local model takes
over for that piece, so a video is never lost to a cloud hiccup."""
import io
import json
import os
import re
import threading
import wave

import httpx
import numpy as np

from . import config

SERVICES = {
    "local": ("This computer (English only, free)", "", ""),
    "openai": ("OpenAI Whisper (any language)", "https://api.openai.com/v1", "whisper-1"),
    "groq": ("Groq Whisper (any language, fast)", "https://api.groq.com/openai/v1", "whisper-large-v3"),
}
CAPTION_MODES = {"english": "English only", "hinglish": "English, with Hindi in Roman letters (Hinglish)"}
PIECE_SECONDS = 600            # 10 minutes of 16 kHz mono WAV is about 19 MB: under the 25 MB upload limit
RATE = 16000

# Whisper answers with the language's name. The captions code works with short codes.
_LANG_CODES = {"english": "en", "hindi": "hi", "urdu": "ur", "spanish": "es", "arabic": "ar", "bengali": "bn",
               "tamil": "ta", "telugu": "te", "marathi": "mr", "gujarati": "gu", "punjabi": "pa", "kannada": "kn",
               "malayalam": "ml", "french": "fr", "german": "de", "portuguese": "pt", "russian": "ru",
               "japanese": "ja", "korean": "ko", "chinese": "zh", "italian": "it", "turkish": "tr",
               "indonesian": "id", "nepali": "ne"}

_lock = threading.Lock()
_saved = {"at": None, "data": {}}


class Words(list):
    """A transcript (list of {'w','s','e'}) that also knows the language it was spoken in, when known."""
    lang = ""


def _file():
    return config.DATA_DIR / "speech.json"


def _from_dashboard() -> dict:
    f = _file()
    try:
        at = f.stat().st_mtime_ns
    except OSError:
        at = 0
    if _saved["at"] != at:
        try:
            data = json.loads(f.read_text(encoding="utf-8")) if at else {}
        except (OSError, ValueError):
            data = {}
        _saved.update(at=at, data=data if isinstance(data, dict) else {})
    return _saved["data"]


def current() -> dict:
    d = _from_dashboard()
    service = str(d.get("service") or config.env("CLIPMAXXING_SPEECH", "local")).strip().lower()
    mode = str(d.get("captions") or config.env("CLIPMAXXING_CAPTION_LANGUAGE", "english")).strip().lower()
    return {"service": service if service in SERVICES else "local",
            "captions": mode if mode in CAPTION_MODES else "english",
            "key": str(d["key"]) if "key" in d else (config.env("CLIPMAXXING_SPEECH_KEY") or "").strip(),
            "model": str(d.get("model") or config.env("CLIPMAXXING_SPEECH_MODEL") or "").strip()}


def caption_mode() -> str:
    return current()["captions"]


def _key(c=None) -> str:
    """The speech key, or the AI key when the AI runs on the same service."""
    c = c or current()
    if c["key"]:
        return c["key"]
    from . import ai
    a = ai.current()
    return a["key"] if a["provider"] == c["service"] else ""


def cloud_ready() -> bool:
    c = current()
    return c["service"] != "local" and bool(_key(c))


def public() -> dict:
    c = current()
    k = _key(c)
    return {"service": c["service"], "captions": c["captions"], "model": c["model"], "has_key": bool(c["key"]),
            "uses_ai_key": bool(k) and not c["key"], "key_hint": k[-4:] if len(k) >= 12 else "",
            "ready": c["service"] == "local" or bool(k),
            "services": [{"id": s, "label": v[0], "example": v[2]} for s, v in SERVICES.items()],
            "caption_modes": [{"id": m, "label": v} for m, v in CAPTION_MODES.items()]}


def save(service, captions, new_key=None, model="") -> dict:
    """`new_key` None keeps the saved key; an empty string removes it (the AI key is then used if it fits)."""
    service = str(service or "local").strip().lower()
    captions = str(captions or "english").strip().lower()
    if service not in SERVICES:
        raise ValueError("Choose one of the speech services in the list.")
    if captions not in CAPTION_MODES:
        raise ValueError("Choose a caption language.")
    model = str(model or "").strip()[:80]
    if model and not re.fullmatch(r"[\w.\-:/]+", model):
        raise ValueError("A model id has letters, digits and . - : / only.")
    old = current()
    k = old["key"] if new_key is None else str(new_key).strip()[:400]
    data = {"service": service, "captions": captions, "model": model, "key": k}
    if service != "local" and not _key({**old, **data}):
        raise ValueError(f"Paste a key for {SERVICES[service][0].split(' (')[0]}, or set the AI to the same service.")
    with _lock:
        f = _file()
        tmp = f.with_suffix(".tmp")
        tmp.write_text(json.dumps(data), encoding="utf-8")
        try:
            os.chmod(tmp, 0o600)
        except OSError:
            pass
        tmp.replace(f)
        _saved["at"] = None
    return public()


# ---------------------------------------------------------------- Whisper over the network
def _wav(audio: np.ndarray) -> bytes:
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(RATE)
        w.writeframes(np.asarray(audio, dtype=np.int16).tobytes())
    return buf.getvalue()


def lang_code(name: str) -> str:
    n = (name or "").strip().lower()
    return _LANG_CODES.get(n, n[:2] if len(n) == 2 else n)


def _whisper_piece(audio: np.ndarray, c: dict, timeout=300) -> tuple[list, str]:
    base, default_model = SERVICES[c["service"]][1], SERVICES[c["service"]][2]
    r = httpx.post(f"{base}/audio/transcriptions", timeout=timeout,
                   headers={"Authorization": f"Bearer {_key(c)}"},
                   files={"file": ("audio.wav", _wav(audio), "audio/wav")},
                   data={"model": c["model"] or default_model, "response_format": "verbose_json",
                         "timestamp_granularities[]": "word"})
    if r.status_code >= 400:
        raise RuntimeError(f"Speech to text failed (HTTP {r.status_code}): {r.text[:200]}")
    body = r.json()
    words = []
    for w in body.get("words") or []:
        text = str(w.get("word") or "").strip()
        if text:
            words.append({"w": text, "s": round(float(w.get("start", 0)), 2), "e": round(float(w.get("end", 0)), 2)})
    if not words:      # some models give sentences only: spread each sentence's words over its time
        for seg in body.get("segments") or []:
            parts = str(seg.get("text") or "").split()
            s, e = float(seg.get("start", 0)), float(seg.get("end", 0))
            step = max(0.05, (e - s) / max(1, len(parts)))
            words += [{"w": p, "s": round(s + i * step, 2), "e": round(s + (i + 1) * step, 2)} for i, p in enumerate(parts)]
    return words, lang_code(body.get("language") or "")


def transcribe_cloud(audio: np.ndarray, on_progress=None, fallback=None) -> Words:
    """The whole audio through Whisper, piece by piece. A piece Whisper fails on goes to `fallback` (the local model)."""
    c = current()
    out, langs = Words(), {}
    total = max(1, len(audio))
    step = PIECE_SECONDS * RATE
    for a in range(0, len(audio), step):
        piece = audio[a:a + step]
        if len(piece) < RATE // 2:
            continue
        try:
            words, lang = _whisper_piece(piece, c)
            if lang:
                langs[lang] = langs.get(lang, 0) + len(piece)
        except Exception:  # noqa: BLE001 - this piece is heard on this machine instead
            if fallback is None:
                raise
            words = fallback(piece)
        off = a / RATE
        out += [dict(w, s=round(w["s"] + off, 2), e=round(w["e"] + off, 2)) for w in words]
        if on_progress:
            on_progress(min(1.0, (a + len(piece)) / total))
    out.lang = max(langs, key=langs.get) if langs else ""
    return out
