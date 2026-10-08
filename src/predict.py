"""Step 4: predictions.csv for the hidden test set, checked against the required format.

Run:  python -m src.predict
Writes predictions.csv (request_id, team) in the project root and docs/expected_score.md.
"""
import os

import numpy as np
import pandas as pd

from src.evaluate import backtest, wilson
from src.train import MODEL_PATH, TARGET, load_train
import joblib

CLEAN, RAW, OUT = "data/clean", "data/raw", "outputs"
BANDS = [0, 0.5, 0.7, 0.9, 1.0]


def check_format(pred):
    sub = pd.read_csv(f"{RAW}/sample_submission.csv")
    teams = set(pd.read_csv(f"{RAW}/teams.csv")["team"])
    problems = []
    if list(pred.columns) != list(sub.columns):
        problems.append(f"columns are {list(pred.columns)}, expected {list(sub.columns)}")
    if len(pred) != len(sub):
        problems.append(f"{len(pred)} rows, expected {len(sub)}")
    if pred.request_id.duplicated().any():
        problems.append("duplicate request_id")
    if set(pred.request_id) != set(sub.request_id):
        problems.append("request_ids do not match sample_submission.csv")
    bad = set(pred.team) - teams
    if bad:
        problems.append(f"team names not in teams.csv: {bad}")
    if problems:
        raise SystemExit("FORMAT CHECK FAILED: " + "; ".join(problems))
    print(f"format check passed: {len(pred)} rows, one per request_id, all teams valid")


def run():
    os.makedirs(OUT, exist_ok=True)
    te = pd.read_csv(f"{CLEAN}/test_clean.csv")
    model = joblib.load(MODEL_PATH)
    P = model.predict_proba(te)
    te["team"] = model.classes_[P.argmax(1)]
    te["conf"] = P.max(1)

    sub = pd.read_csv(f"{RAW}/sample_submission.csv")
    pred = te[["request_id", "team"]].set_index("request_id").loc[sub.request_id].reset_index()
    check_format(pred)
    pred.to_csv("predictions.csv", index=False)

    # Expected score. Backtest accuracy per confidence band, weighted by how many test requests fall in each band.
    v = backtest(load_train())
    v["ok"] = v.pred == v[TARGET]
    LABELS = ["under 0.5", "0.5 to 0.7", "0.7 to 0.9", "0.9 or more"]
    v["band"] = pd.cut(v.conf, BANDS, include_lowest=True, labels=LABELS)
    te["band"] = pd.cut(te.conf, BANDS, include_lowest=True, labels=LABELS)
    acc_by_band = v.groupby("band", observed=True).ok.mean()
    conf_by_band = v.groupby("band", observed=True).conf.mean()
    share = te.band.value_counts(normalize=True).sort_index()
    expected = float((share * acc_by_band).sum())
    plain = v.ok.mean()
    lo, hi = wilson(int(v.ok.sum()), len(v))
    lo, hi = lo - 0.005, hi + 0.005          # widened half a point for drift in the test months
    sure_wrong = float(((~v.ok) & (v.conf >= 0.9)).mean())
    match_bot = float((v.pred == v.bot_team).mean())   # how often the model's pick equals the bot's queue
    auto = te.conf >= 0.7
    lines = [
        "# Expected score (written before submitting predictions.csv)\n",
        "**Metric:** accuracy, the share of test requests sent to the team where they actually ended up (`final_team`). "
        "I chose it because that is what the business pays for: each wrong destination costs Rs 305 per transfer plus an extra contact (Rs 260).\n",
        f"**Expected: {expected:.1%}**, most likely between {lo:.1%} and {hi:.1%} (the 95% range from the backtests, widened by half a point for drift).\n",
        "## How I estimated it\n",
        f"1. Backtests: trained only on earlier requests and tested on the next 3 months, 3 times ({len(v):,} requests). Plain accuracy {plain:.1%}.",
        "2. The test set has a different mix of clear and vague messages, so I weighted the backtest accuracy of each confidence band "
        "by how many test requests fall in that band:\n",
        "| Confidence band | Share of test requests | Accuracy in backtests |\n|---|---|---|",
    ]
    for b in share.index:
        lines.append(f"| {b} | {share[b]:.1%} | {acc_by_band[b]:.1%} |")
    lines += [
        f"\nTest requests the model would route automatically (confidence 0.7 or more): {auto.mean():.1%}.\n",
        "## What could make the real score lower\n",
        "- The test months (Jul to Sep 2026) are all after the CRM switch and I have no labels to check drift.",
        f"- The model is overconfident when it is unsure: in the 0.5 to 0.7 band it averages {conf_by_band['0.5 to 0.7']:.0%} confidence but is right {acc_by_band['0.5 to 0.7']:.0%} of the time. So I did not use its own confidence as the estimate.",
        f"- If the hidden outcome is the bot's queue rather than the final team, expect about {match_bot:.0%}.",
        f"- About {sure_wrong:.1%} of requests (1 in {round(1 / sure_wrong)}) end up somewhere the model was very sure was wrong, so those cannot be fixed by a better model.",
    ]
    open("docs/expected_score.md", "w", encoding="utf-8").write("\n".join(lines) + "\n")
    print("\n".join(lines))
    print("\nteam counts in predictions:\n", pred.team.value_counts().to_string())


if __name__ == "__main__":
    run()
