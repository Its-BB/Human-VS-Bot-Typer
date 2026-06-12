from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Literal

Mode = Literal["human", "automated"]
BotKind = Literal["fixed", "jitter", "fake_hum"]

SNIPS = [
    "The mitochondria is the powerhouse of the cell.",
    "Photosynthesis converts light energy into chemical energy.",
    "Newton's first law describes inertia and motion.",
    "The water cycle includes evaporation and precipitation.",
    "DNA carries genetic information in living organisms.",
    "Supply and demand determine market equilibrium prices.",
    "The French Revolution began in seventeen eighty-nine.",
    "Algorithms must balance time complexity and memory usage.",
    "Encryption protects data in transit and at rest.",
    "Machine learning models generalize from training samples.",
]

TYPO = {"a": "s", "e": "r", "i": "o", "o": "p", "t": "r", "s": "a", "n": "m", "r": "t", "h": "j", "l": "k"}
FAST_PAIRS = {
    "th", "he", "in", "er", "an", "on", "at", "en", "es", "ed",
    "or", "te", "of", "it", "is", "al", "ar", "st", "nt", "re",
}


@dataclass
class KeystrokeEvent:
    key: str
    action: Literal["press", "release"]
    t_ms: int
    is_error: bool = False


@dataclass
class TypingSession:
    text: str
    events: list[KeystrokeEvent] = field(default_factory=list)
    wpm: float = 0.0
    error_count: int = 0
    corrections: int = 0
    mode: Mode = "human"
    profile: str = "default"


def rnd_snip() -> str:
    return random.choice(SNIPS)


def _mk_pr(key: str, t: int, dwell: int, err: bool = False) -> list[KeystrokeEvent]:
    return [
        KeystrokeEvent(key=key, action="press", t_ms=t, is_error=err),
        KeystrokeEvent(key=key, action="release", t_ms=t + dwell, is_error=err),
    ]


def _pair(prev: str, ch: str) -> str:
    if not prev or prev == " ":
        return ""
    return (prev + ch).lower()


def _hum_dly(base: float, prev: str, ch: str, pos: int, n: int, burst: float) -> int:
    d = random.lognormvariate(0, 0.35) * base * burst
    pair = _pair(prev, ch)
    if pair in FAST_PAIRS:
        d *= random.uniform(0.55, 0.85)
    if ch == " ":
        d += random.uniform(90, 280)
    if ch in ".,!?;:":
        d += random.uniform(120, 380)
    if ch.isupper():
        d += random.uniform(50, 140)
    if random.random() < 0.04:
        d += random.uniform(300, 900)
    d *= 1.0 + (pos / max(n, 1)) * random.uniform(0.0, 0.18)
    return max(35, int(d))


def _hum_dwl(ch: str) -> int:
    base = 88 if ch.isalpha() else 105
    return max(42, int(random.gauss(base, 28)))


def _bot_dly(kind: BotKind, base: float, prev: str, ch: str) -> int:
    if kind == "fixed":
        return max(28, int(base))
    if kind == "jitter":
        return max(26, int(base + random.uniform(-4, 4)))
    d = base + random.gauss(0, base * 0.08)
    if ch == " ":
        d += random.uniform(20, 60)
    if _pair(prev, ch) in FAST_PAIRS:
        d *= 0.92
    return max(30, int(d))


def _bot_dwl(kind: BotKind) -> int:
    if kind == "fixed":
        return 68
    if kind == "jitter":
        return max(34, int(68 + random.uniform(-3, 3)))
    return max(40, int(random.gauss(82, 8)))


def _maybe_typo(ch: str, rate: float) -> str | None:
    if not ch.isalpha() or random.random() >= rate:
        return None
    bad = TYPO.get(ch.lower(), random.choice(list(TYPO.values())))
    return bad.upper() if ch.isupper() else bad


def gen_human(text: str) -> TypingSession:
    evs: list[KeystrokeEvent] = []
    t, errs, fixes = 0, 0, 0
    base = random.uniform(95, 175)
    err_rate = random.uniform(0.04, 0.09)
    burst = random.uniform(0.85, 1.15)
    prev = ""
    prof = random.choice(["steady", "bursty", "careful"])

    for i, ch in enumerate(text):
        if prof == "bursty" and i > 0 and i % random.randint(8, 16) == 0:
            t += random.randint(250, 700)

        bad = _maybe_typo(ch, err_rate if prof != "careful" else err_rate * 1.4)
        if bad:
            dw = _hum_dwl(ch)
            evs.extend(_mk_pr(bad, t, dw, True))
            errs += 1
            t += dw + random.randint(200, 650)
            bdw = _hum_dwl("Backspace")
            evs.extend(_mk_pr("Backspace", t, bdw))
            t += bdw + _hum_dly(base * 0.75, prev, ch, i, len(text), burst)
            fixes += 1

        dw = _hum_dwl(ch)
        evs.extend(_mk_pr(ch, t, dw))
        t += dw
        if i < len(text) - 1:
            t += _hum_dly(base, ch, text[i + 1], i, len(text), burst)
        prev = ch

    s = TypingSession(text=text, events=evs, error_count=errs, corrections=fixes, mode="human", profile=prof)
    s.wpm = calc_stats(evs)["wpm"]
    return s


def gen_bot(text: str, kind: BotKind | None = None) -> TypingSession:
    kind = kind or random.choice(["fixed", "jitter", "fake_hum"])
    evs: list[KeystrokeEvent] = []
    t = 0
    base = random.uniform(52, 78) if kind != "fake_hum" else random.uniform(88, 130)
    prev = ""
    dw = _bot_dwl(kind)

    for i, ch in enumerate(text):
        if kind == "fake_hum" and random.random() < 0.012:
            t += random.randint(80, 200)
        evs.extend(_mk_pr(ch, t, dw))
        t += dw
        if i < len(text) - 1:
            t += _bot_dly(kind, base, ch, text[i + 1])
        prev = ch
        if kind != "fixed":
            dw = _bot_dwl(kind)

    s = TypingSession(text=text, events=evs, mode="automated", profile=kind)
    s.wpm = calc_stats(evs)["wpm"]
    return s


def gen_sess(text: str, mode: Mode) -> TypingSession:
    return gen_human(text) if mode == "human" else gen_bot(text)


def calc_stats(evs: list[KeystrokeEvent]) -> dict:
    prs = [e for e in evs if e.action == "press" and e.key != "Backspace"]
    if not prs:
        return {"wpm": 0.0, "error_count": 0, "elapsed_ms": 0, "char_count": 0}
    elapsed = max(prs[-1].t_ms, 1)
    n = len(prs)
    return {
        "wpm": round((n / elapsed) * 60000 / 5, 1),
        "error_count": sum(1 for e in prs if e.is_error),
        "elapsed_ms": elapsed,
        "char_count": n,
    }


def to_client(evs: list[KeystrokeEvent]) -> list[dict]:
    return [{"key": e.key, "action": e.action, "t_ms": e.t_ms, "is_error": e.is_error} for e in evs]


def sess_to_dict(s: TypingSession) -> dict:
    return {
        "text": s.text,
        "mode": s.mode,
        "profile": s.profile,
        "wpm": s.wpm,
        "error_count": s.error_count,
        "corrections": s.corrections,
        "events": to_client(s.events),
    }


def sess_from_dict(d: dict) -> TypingSession:
    evs = [
        KeystrokeEvent(key=e["key"], action=e["action"], t_ms=e["t_ms"], is_error=e.get("is_error", False))
        for e in d["events"]
    ]
    return TypingSession(
        text=d["text"],
        events=evs,
        wpm=d.get("wpm", 0.0),
        error_count=d.get("error_count", 0),
        corrections=d.get("corrections", 0),
        mode=d["mode"],
        profile=d.get("profile", "default"),
    )
