"""Step 3: evidence that it works, and how often it does not.

Time-based backtests: train only on the past, test on the next 3 months. The real test set follows
the training data in time, so a random split would flatter the model.

Run:  python -m src.evaluate
"""
import math
import os

import numpy as np
import pandas as pd
from sklearn.metrics import f1_score

from src.train import TARGET, build_model, load_train

FOLDS = [("2025-10-01", "2026-01-01"), ("2026-01-01", "2026-04-01"), ("2026-04-01", "2026-07-01")]
THRESHOLDS = [0.5, 0.6, 0.7, 0.8, 0.9]


def wilson(k, n, z=1.96):
    p = k / n
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    r = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return (c - r) / d, (c + r) / d


def backtest(tr):
    parts = []
    for a, b in FOLDS:
        fit = tr[tr.created_at < a]
        val = tr[(tr.created_at >= a) & (tr.created_at < b)].copy()
        m = build_model().fit(fit, fit[TARGET])
        P = m.predict_proba(val)
        val["pred"] = m.classes_[P.argmax(1)]
        val["conf"] = P.max(1)
        # the trap: a model trained to copy the bot's labels
        bot_copy = build_model().fit(fit, fit["bot_team"])
        val["pred_botcopy"] = bot_copy.predict(val)
        val["fold"] = f"{a} to {b}"
        parts.append(val)
    return pd.concat(parts)


def run():
    os.makedirs("eval", exist_ok=True)
    tr = load_train()
    v = backtest(tr)
    v["ok"] = v.pred == v[TARGET]
    n = len(v)
    L = []
    L.append("# Evidence report\n")
    L.append(f"Time-based backtests on {n:,} requests (3 folds, each trained only on earlier requests). Target: `final_team`.\n")

    L.append("## 1. Accuracy against where requests really ended up\n")
    L.append("| Fold (test window) | Requests | Bot's own label | Model | Model macro-F1 |\n|---|---|---|---|---|")
    for f, g in v.groupby("fold"):
        L.append(f"| {f} | {len(g):,} | {(g.bot_team == g[TARGET]).mean():.1%} | {g.ok.mean():.1%} | {f1_score(g[TARGET], g.pred, average='macro'):.3f} |")
    lo, hi = wilson(int(v.ok.sum()), n)
    bl, bh = wilson(int((v.bot_team == v[TARGET]).sum()), n)
    L.append(f"| **All folds** | **{n:,}** | **{(v.bot_team == v[TARGET]).mean():.1%}** ({bl:.1%} to {bh:.1%}) | **{v.ok.mean():.1%}** ({lo:.1%} to {hi:.1%}) | {f1_score(v[TARGET], v.pred, average='macro'):.3f} |\n")

    L.append("## 2. The 90% target in the brief: matching the bot's labels\n")
    L.append("| Model trained on | Matches the bot's label | Reaches the real destination |\n|---|---|---|")
    L.append(f"| The bot's labels (what the brief asked for) | {(v.pred_botcopy == v.bot_team).mean():.1%} | {(v.pred_botcopy == v[TARGET]).mean():.1%} |")
    L.append(f"| Where requests ended up (`final_team`) | {(v.pred == v.bot_team).mean():.1%} | {v.ok.mean():.1%} |\n")

    L.append("## 3. Confidence: when to trust it\n")
    L.append("| Auto-route only when confidence is at least | Requests auto-routed | Accuracy on those | Left for a person |\n|---|---|---|---|")
    for t in [0.0] + THRESHOLDS:
        s = v[v.conf >= t]
        L.append(f"| {t:.1f} | {len(s) / n:.1%} | {s.ok.mean():.1%} | {1 - len(s) / n:.1%} |")
    v["band"] = pd.cut(v.conf, [0, .5, .7, .9, 1.0])
    L.append("\n| Confidence band | Requests | Accuracy | Mean confidence |\n|---|---|---|---|")
    for b, g in v.groupby("band", observed=True):
        L.append(f"| {b} | {len(g):,} | {g.ok.mean():.1%} | {g.conf.mean():.1%} |")
    L.append("")

    L.append("## 4. How it gets it wrong\n")
    vague = v[~v.ok & (v.conf < 0.5)]
    mid = v[~v.ok & (v.conf >= 0.5) & (v.conf < 0.9)]
    sure = v[~v.ok & (v.conf >= 0.9)]
    L.append("| Kind of error | Count | Share of all errors |\n|---|---|---|")
    ne = (~v.ok).sum()
    L.append(f"| Vague message, model unsure (confidence under 0.5) | {len(vague):,} | {len(vague) / ne:.0%} |")
    L.append(f"| Partly clear, model fairly unsure (0.5 to 0.9) | {len(mid):,} | {len(mid) / ne:.0%} |")
    L.append(f"| Model very sure (0.9 or more) but the destination differs | {len(sure):,} | {len(sure) / ne:.0%} |")
    L.append("\nPer team, share of requests sent to the right team:\n\n| Team | Requests | Recall |\n|---|---|---|")
    for t, g in v.groupby(TARGET):
        L.append(f"| {t} | {len(g):,} | {g.ok.mean():.1%} |")
    L.append("")
    open("eval/report.md", "w", encoding="utf-8").write("\n".join(L))

    pd.crosstab(v[TARGET], v.pred).to_csv("eval/confusion_matrix.csv")
    cols = ["request_id", "created_at_ist", "channel", "product_family", "warranty_status", "request_text",
            "bot_team", TARGET, "pred", "conf"]
    v[~v.ok][cols].sort_values("conf").to_csv("eval/errors.csv", index=False)
    print("\n".join(L))
    return v


if __name__ == "__main__":
    run()
