from __future__ import annotations

import random
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

import joblib
import numpy as np
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.model_selection import cross_val_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

if TYPE_CHECKING:
    from human_typer import TypingSession

FEATS = [
    "iki_mean", "iki_std", "iki_cv", "iki_skew", "iki_autocorr",
    "dwell_mean", "dwell_std", "dwell_cv", "flight_mean", "flight_std",
    "error_rate", "corr_lat_mean", "corr_lat_std", "bs_ratio",
    "pause_count", "pause_ratio", "burst_count",
    "wpm_var3", "iki_entropy", "rhythm_regularity",
]

@dataclass
class ModelBundle:
    pipe: Pipeline
    cv_acc: float
    feat_imp: dict[str, float]


_ROOT = Path(__file__).resolve().parent
MODEL_PATH = _ROOT / "models" / "bundle.joblib"
_MODEL_PATHS = [MODEL_PATH, _ROOT / "api" / "models" / "bundle.joblib"]
_bundle: ModelBundle | None = None


def _prs(evs) -> list[tuple[str, int, bool]]:
    return [(e.key, e.t_ms, e.is_error) for e in evs if e.action == "press"]


def _ikis(prs: list[tuple[str, int, bool]]) -> list[float]:
    c = [(k, t) for k, t, _ in prs if k != "Backspace"]
    return [float(c[i][1] - c[i - 1][1]) for i in range(1, len(c))] if len(c) > 1 else []


def _dwls(evs) -> list[float]:
    out, held = [], {}
    for e in evs:
        if e.action == "press":
            held[e.key] = e.t_ms
        elif e.action == "release" and e.key in held:
            out.append(float(e.t_ms - held[e.key]))
            del held[e.key]
    return out


def _flights(evs) -> list[float]:
    out, rel = [], {}
    for e in evs:
        if e.action == "release":
            rel[e.key] = e.t_ms
        elif e.action == "press" and e.key in rel:
            out.append(float(e.t_ms - rel[e.key]))
            del rel[e.key]
    return out


def _corr_lat(evs) -> list[float]:
    out, err_t = [], None
    for e in evs:
        if e.action == "press" and e.is_error:
            err_t = e.t_ms
        elif e.action == "press" and e.key == "Backspace" and err_t is not None:
            out.append(float(e.t_ms - err_t))
            err_t = None
    return out


def _wpm_var3(prs: list[tuple[str, int, bool]]) -> float:
    c = [(k, t) for k, t, _ in prs if k != "Backspace"]
    if len(c) < 6:
        return 0.0
    third = max(len(c) // 3, 1)
    chunks = [c[:third], c[third : 2 * third], c[2 * third :]]
    wpms = []
    for chunk in chunks:
        if len(chunk) < 2:
            continue
        span = max(chunk[-1][1] - chunk[0][1], 1)
        wpms.append((len(chunk) / span) * 60000 / 5)
    return float(np.var(wpms)) if len(wpms) > 1 else 0.0


def _autocorr(xs: list[float]) -> float:
    if len(xs) < 4:
        return 0.0
    a = np.array(xs[:-1])
    b = np.array(xs[1:])
    if a.std() < 1e-6 or b.std() < 1e-6:
        return 0.0
    return float(np.corrcoef(a, b)[0, 1])

def _entropy(xs: list[float]) -> float:
    if len(xs) < 3:
        return 0.0
    hist, _ = np.histogram(xs, bins=8)
    p = hist / max(hist.sum(), 1)
    p = p[p > 0]
    return float(-np.sum(p * np.log2(p)))


def _safe_skew(xs: list[float]) -> float:
    if len(xs) < 3:
        return 0.0
    return float(np.mean(((np.array(xs) - np.mean(xs)) / (np.std(xs) + 1e-6)) ** 3))


def ext_feats(sess: TypingSession) -> dict:
    prs = _prs(sess.events)
    ikis = _ikis(prs)
    dwls = _dwls(sess.events)
    flts = _flights(sess.events)
    corr = _corr_lat(sess.events)
    content = [p for p in prs if p[0] != "Backspace"]
    n = max(len(content), 1)
    bs = sum(1 for p in prs if p[0] == "Backspace")
    iki_m = float(np.mean(ikis)) if ikis else 0.0
    iki_s = float(np.std(ikis)) if ikis else 0.0
    dwl_m = float(np.mean(dwls)) if dwls else 0.0
    dwl_s = float(np.std(dwls)) if dwls else 0.0
    flt_m = float(np.mean(flts)) if flts else 0.0
    flt_s = float(np.std(flts)) if flts else 0.0
    pauses = [x for x in ikis if x > 400]
    bursts = [x for x in ikis if x < 50]

    return {
        "iki_mean": round(iki_m, 1),
        "iki_std": round(iki_s, 1),
        "iki_cv": round(iki_s / iki_m, 4) if iki_m else 0.0,
        "iki_skew": round(_safe_skew(ikis), 3),
        "iki_autocorr": round(_autocorr(ikis), 3),
        "dwell_mean": round(dwl_m, 1),
        "dwell_std": round(dwl_s, 1),
        "dwell_cv": round(dwl_s / dwl_m, 4) if dwl_m else 0.0,
        "flight_mean": round(flt_m, 1),
        "flight_std": round(flt_s, 1),
        "error_rate": round(sess.error_count / n, 4),
        "corr_lat_mean": round(float(np.mean(corr)), 1) if corr else 0.0,
        "corr_lat_std": round(float(np.std(corr)), 1) if len(corr) > 1 else 0.0,
        "bs_ratio": round(bs / n, 4),
        "pause_count": len(pauses),
        "pause_ratio": round(len(pauses) / max(len(ikis), 1), 4),
        "burst_count": len(bursts),
        "wpm_var3": round(_wpm_var3(prs), 2),
        "iki_entropy": round(_entropy(ikis), 3),
        "rhythm_regularity": round(1.0 / (iki_s + 1e-6), 5),
    }


def _vec(f: dict) -> list[float]:
    return [f[k] for k in FEATS]


def _rule_score(f: dict) -> float:
    s = 0.5
    if f["iki_cv"] > 0.2:
        s += 0.12
    elif f["iki_cv"] < 0.1:
        s -= 0.14
    if f["pause_count"] >= 2:
        s += 0.1
    elif f["pause_count"] == 0 and f["iki_cv"] < 0.12:
        s -= 0.08
    if f["error_rate"] > 0:
        s += 0.12
    elif f["error_rate"] == 0 and f["iki_cv"] < 0.14:
        s -= 0.06
    if f["dwell_cv"] > 0.22:
        s += 0.08
    elif f["dwell_cv"] < 0.08:
        s -= 0.1
    if f["iki_autocorr"] > 0.15:
        s += 0.06
    elif f["iki_autocorr"] < -0.05 and f["iki_cv"] < 0.15:
        s -= 0.05
    if f["wpm_var3"] > 35:
        s += 0.07
    elif f["wpm_var3"] < 12 and f["iki_cv"] < 0.14:
        s -= 0.07
    if f["rhythm_regularity"] > 0.025:
        s -= 0.1
    return max(0.0, min(1.0, s))


def _reasons(f: dict, imp: dict[str, float]) -> list[str]:
    r = []
    if f["iki_cv"] < 0.11:
        r.append(f"Low IKI variance (CV={f['iki_cv']:.3f})")
    elif f["iki_cv"] > 0.22:
        r.append(f"High IKI variance (CV={f['iki_cv']:.3f})")
    if f["pause_count"] >= 2:
        r.append(f"{f['pause_count']} pauses over 400ms")
    elif f["pause_count"] == 0 and f["iki_cv"] < 0.12:
        r.append("No natural pauses")
    if f["error_rate"] > 0:
        r.append(f"Errors present ({f['error_rate']*100:.1f}%)")
    elif f["error_rate"] == 0 and f["iki_cv"] < 0.13:
        r.append("Perfect accuracy with flat rhythm")
    if f["dwell_cv"] < 0.09:
        r.append(f"Uniform dwell times (CV={f['dwell_cv']:.3f})")
    elif f["dwell_cv"] > 0.25:
        r.append(f"Varied dwell times (CV={f['dwell_cv']:.3f})")
    if f["iki_autocorr"] > 0.2:
        r.append("Natural rhythm autocorrelation")
    if f["rhythm_regularity"] > 0.03:
        r.append("Metronome-like regularity")
    top = sorted(imp.items(), key=lambda x: x[1], reverse=True)[:2]
    for name, w in top:
        if w > 0.05:
            r.append(f"Key signal: {name} ({w:.0%} importance)")
    return r[:6]


def _gen_set(n: int) -> tuple[list[list[float]], list[int]]:
    from human_typer import SNIPS, gen_bot, gen_human

    X, y = [], []
    for _ in range(n):
        t = random.choice(SNIPS)
        X.append(_vec(ext_feats(gen_human(t))))
        y.append(1)
        X.append(_vec(ext_feats(gen_bot(t))))
        y.append(0)
    return X, y


def _train() -> ModelBundle:
    X, y = _gen_set(300)
    Xa = np.array(X)
    ya = np.array(y)

    rf = RandomForestClassifier(n_estimators=100, max_depth=12, min_samples_leaf=2, random_state=42)
    cv = float(np.mean(cross_val_score(rf, Xa, ya, cv=5)))
    rf.fit(Xa, ya)
    imp = {k: float(v) for k, v in zip(FEATS, rf.feature_importances_)}

    gb = GradientBoostingClassifier(n_estimators=60, max_depth=4, learning_rate=0.1, random_state=42)
    pipe = Pipeline([("sc", StandardScaler()), ("gb", gb)])
    pipe.fit(Xa, ya)

    return ModelBundle(pipe=pipe, cv_acc=round(cv, 4), feat_imp=imp)


def save_model(path: Path | None = None) -> ModelBundle:
    path = path or MODEL_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    b = _train()
    joblib.dump(b, path)
    return b


def _load_disk() -> ModelBundle | None:
    for p in _MODEL_PATHS:
        if p.is_file():
            return joblib.load(p)
    return None


def _get_bundle() -> ModelBundle:
    global _bundle
    if _bundle is None:
        _bundle = _load_disk() or _train()
    return _bundle


def warmup() -> dict:
    b = _get_bundle()
    return {"cv_accuracy": b.cv_acc, "features": len(FEATS)}


def pred(sess: TypingSession) -> dict:
    f = ext_feats(sess)
    b = _get_bundle()
    ml_hum = float(b.pipe.predict_proba(np.array([_vec(f)]))[0][1])
    rule_hum = _rule_score(f)
    hum = 0.72 * ml_hum + 0.28 * rule_hum
    lbl = "human" if hum >= 0.5 else "automated"
    conf = hum if lbl == "human" else 1.0 - hum
    agree = (ml_hum >= 0.5) == (rule_hum >= 0.5)
    return {
        "label": lbl,
        "confidence": round(conf * 100, 1),
        "ml_score": round(ml_hum * 100, 1),
        "rule_score": round(rule_hum * 100, 1),
        "models_agree": agree,
        "reasons": _reasons(f, b.feat_imp),
        "features": f,
    }
