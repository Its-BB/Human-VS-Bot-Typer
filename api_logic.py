import random

from human_typer import Mode, calc_stats, gen_sess, rnd_snip, sess_from_dict, sess_to_dict, to_client
from lib.session import open as open_token, seal
from timing_model import pred, warmup


def create_round() -> dict:
    text = rnd_snip()
    mode: Mode = "human" if random.random() < 0.5 else "automated"
    sess = gen_sess(text, mode)
    st = calc_stats(sess.events)
    token = seal(sess_to_dict(sess))
    return {
        "round_id": token,
        "events": to_client(sess.events),
        "snippet_length": len(text),
        "duration_ms": st["elapsed_ms"],
    }


def process_guess(token: str | None, guess: str) -> tuple[dict, int]:
    g = (guess or "").strip().lower()
    if g not in ("human", "automated"):
        return {"error": "guess must be human or automated"}, 400
    if not token:
        return {"error": "round_id required"}, 400
    try:
        payload = open_token(token)
    except Exception:
        return {"error": "round not found or expired"}, 404

    sess = sess_from_dict(payload)
    actual = payload["mode"]
    ok = g == actual
    m = pred(sess)
    st = calc_stats(sess.events)
    f = m["features"]
    return {
        "correct": ok,
        "actual": actual,
        "profile": sess.profile,
        "model_label": m["label"],
        "model_confidence": m["confidence"],
        "ml_score": m["ml_score"],
        "rule_score": m["rule_score"],
        "models_agree": m["models_agree"],
        "reasons": m["reasons"],
        "stats": {
            "wpm": st["wpm"],
            "errors": sess.error_count,
            "corrections": sess.corrections,
            "elapsed_ms": st["elapsed_ms"],
            "mean_iki": f["iki_mean"],
            "timing_cv": f["iki_cv"],
            "dwell_cv": f["dwell_cv"],
            "pause_count": f["pause_count"],
            "iki_autocorr": f["iki_autocorr"],
        },
    }, 200


def health_info() -> dict:
    w = warmup()
    return {"ok": True, "model_cv_accuracy": w["cv_accuracy"], "feature_count": w["features"]}
