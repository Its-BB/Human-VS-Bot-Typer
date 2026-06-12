const $ = (id) => document.getElementById(id);
const typed = $("typed");
const wpmEl = $("wpm");
const errsEl = $("errs");
const progEl = $("prog");
const resEl = $("res");
const scoreEl = $("score");
const roundsEl = $("rounds");
const btnNew = $("btn-new");
const btnHum = $("btn-hum");
const btnBot = $("btn-bot");

let rid = null, replaying = false, abort = false, score = 0, rounds = 0;

const esc = (s) => s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

const setGuess = (on) => {
  btnHum.disabled = !on;
  btnBot.disabled = !on;
};

const render = (txt, err) => {
  if (!txt) {
    typed.innerHTML = '<span class="cur"></span>';
    return;
  }
  if (err) {
    typed.innerHTML = `${esc(txt.slice(0, -1))}<span class="err">${esc(txt.slice(-1))}</span><span class="cur"></span>`;
  } else {
    typed.innerHTML = `${esc(txt)}<span class="cur"></span>`;
  }
};

const reset = () => {
  render("");
  wpmEl.textContent = "-";
  errsEl.textContent = "-";
  progEl.textContent = "0%";
  resEl.classList.add("hide");
  setGuess(false);
};

const replay = async (evs, len) => {
  replaying = true;
  let txt = "", errs = 0, n = 0;
  render("");
  for (let i = 0; i < evs.length; i++) {
    if (abort) return;
    const ev = evs[i];
    const prev = i ? evs[i - 1] : null;
    const d = prev ? Math.max(0, ev.t_ms - prev.t_ms) : 0;
    if (d) await sleep(d);
    if (ev.action !== "press") continue;
    if (ev.key === "Backspace") {
      txt = txt.slice(0, -1);
      n = Math.max(0, n - 1);
    } else {
      txt += ev.key;
      n++;
      if (ev.is_error) errs++;
    }
    render(txt, ev.is_error);
    wpmEl.textContent = String(Math.round(((n / Math.max(ev.t_ms, 1)) * 60000) / 5));
    errsEl.textContent = String(errs);
    progEl.textContent = `${Math.min(100, Math.round((n / len) * 100))}%`;
  }
};

const start = async () => {
  if (replaying) return;
  abort = true;
  await sleep(30);
  abort = false;
  reset();
  btnNew.disabled = true;
  try {
    const r = await fetch("/api/round", { method: "POST" });
    const d = await r.json();
    if (!r.ok) throw new Error(d.error || "failed");
    rid = d.round_id;
    await replay(d.events, d.snippet_length);
    if (!abort) setGuess(true);
  } catch (e) {
    typed.textContent = e.message;
  } finally {
    btnNew.disabled = false;
    replaying = false;
  }
};

const guess = async (g) => {
  if (!rid || replaying) return;
  setGuess(false);
  try {
    const r = await fetch("/api/guess", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ round_id: rid, guess: g }),
    });
    const d = await r.json();
    if (!r.ok) throw new Error(d.error || "failed");
    rounds++;
    if (d.correct) score++;
    scoreEl.textContent = score;
    roundsEl.textContent = rounds;
    const s = d.stats || {};
    resEl.classList.remove("hide");
    resEl.innerHTML = [
      `<p><b>${d.correct ? "Correct" : "Wrong"}</b> — actual: ${d.actual} (${d.profile || "-"})</p>`,
      `<p>Model: ${d.model_label} (${d.model_confidence}%) · ML ${d.ml_score}% · rules ${d.rule_score}%</p>`,
      `<ul>${(d.reasons || []).map((x) => `<li>${esc(x)}</li>`).join("")}</ul>`,
      `<p>WPM ${s.wpm} · errors ${s.errors} · IKI ${s.mean_iki}ms · CV ${s.timing_cv} · pauses ${s.pause_count} · autocorr ${s.iki_autocorr}</p>`,
    ].join("");
    rid = null;
  } catch (e) {
    resEl.classList.remove("hide");
    resEl.innerHTML = `<p>${esc(e.message)}</p>`;
  }
};

btnNew.onclick = start;
btnHum.onclick = () => guess("human");
btnBot.onclick = () => guess("automated");
