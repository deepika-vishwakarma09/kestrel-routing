"""Step 5: the rupees and the busiest teams. Writes outputs/findings.txt and two charts.

All costs are from ops-policy section 4. Assumptions are written next to the numbers.
Run:  python -m src.business
"""
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from src.evaluate import backtest
from src.train import TARGET, load_train

TRANSFER, EXTRA_CONTACT, LICENCE_YEAR = 305, 260, 320000
PERSON_COST = 260        # assumption: a person reading or calling about a vague request costs one contact (policy section 4)
AUTO_AT = 0.70


def run():
    os.makedirs("outputs/charts", exist_ok=True)
    tr = load_train()
    te = pd.read_csv("data/clean/test_clean.csv")
    n_train_months = tr.created_at.dt.to_period("M").nunique()
    n_test_months = pd.to_datetime(te.created_at_ist).dt.to_period("M").nunique()
    volume = len(te) / n_test_months                       # requests per month, latest quarter
    L = []

    # 1. Which teams are busiest
    L.append("BUSIEST TEAMS (requests per month, where requests really ended up)")
    bot = tr.bot_team.value_counts() / n_train_months
    fin = tr.final_team.value_counts() / n_train_months
    inflow = tr[tr.final_team != tr.first_team].final_team.value_counts() / n_train_months
    t = pd.DataFrame({"bot_queue": bot, "ended_up_here": fin, "arrived_by_transfer": inflow}).fillna(0).round(0).astype(int)
    t["difference"] = t.ended_up_here - t.bot_queue
    L.append(t.sort_values("ended_up_here", ascending=False).to_string())
    L.append("There is no staffing file in the Kestrel pack, so this is demand per team, not load per person.\n")

    # 2. What a wrong routing costs
    wrong = tr.bot_team != tr.final_team
    per_wrong = tr[wrong].transfers.mean() * TRANSFER + EXTRA_CONTACT
    L.append("COST OF A WRONG ROUTING")
    L.append(f"Bot sends {wrong.mean():.1%} of requests to the wrong team. Each such request needs {tr[wrong].transfers.mean():.2f} transfers on average "
             f"({tr[wrong].transfers.mean():.2f} x Rs {TRANSFER}) plus one extra customer contact (Rs {EXTRA_CONTACT}) = Rs {per_wrong:.0f}.")
    L.append(f"Bot misrouting at {volume:.0f} requests a month: Rs {wrong.mean() * volume * per_wrong:,.0f} a month, "
             f"on top of the licence (Rs {LICENCE_YEAR / 12:,.0f} a month).")
    L.append(f"{tr[wrong].transfers.sum() / tr.transfers.sum():.0%} of all transfers come from the bot's wrong routings.\n")

    # 3. Three ways to run it, same volume
    v = backtest(tr)
    v["ok"] = v.pred == v[TARGET]
    auto = v.conf >= AUTO_AT
    model_err, auto_share, auto_err = 1 - v.ok.mean(), auto.mean(), 1 - v[auto].ok.mean()
    bot_cost = wrong.mean() * volume * per_wrong
    all_auto = model_err * volume * per_wrong
    hybrid_wrong = auto_share * volume * auto_err * per_wrong
    hybrid_people = (1 - auto_share) * volume * PERSON_COST
    hybrid = hybrid_wrong + hybrid_people
    breakeven = (all_auto - hybrid_wrong) / ((1 - auto_share) * volume)
    L.append(f"THREE WAYS TO RUN IT (monthly, {volume:.0f} requests)")
    rows = [
        ("Keep the bot", wrong.mean(), bot_cost, LICENCE_YEAR / 12),
        ("Model routes everything", model_err, all_auto, 0),
        (f"Model routes when sure (confidence {AUTO_AT:.1f}+), a person reads the rest", auto_err * auto_share + (1 - auto_share) * 0, hybrid, 0),
    ]
    L.append(f"{'Option':72s} {'Misrouting + handling':>22s} {'Licence':>9s} {'Total':>10s} {'Saving vs bot':>14s}")
    base = bot_cost + LICENCE_YEAR / 12
    for name, _, cost, lic in rows:
        L.append(f"{name:72s} {cost:>22,.0f} {lic:>9,.0f} {cost + lic:>10,.0f} {round(base - cost - lic) + 0:>14,}")
    L.append(f"\nSaving per year: model routes everything Rs {(base - all_auto) * 12 / 100000:.1f} lakh; "
             f"model plus person for the unsure ones Rs {(base - hybrid) * 12 / 100000:.1f} lakh.")
    L.append(f"In the last option the model sends {auto_share:.1%} of requests automatically at {1 - auto_err:.1%} accuracy; "
             f"{1 - auto_share:.1%} ({(1 - auto_share) * volume:.0f} a month) go to a person.")
    L.append(f"Assumptions: the model's wrong routings cost the same as the bot's (Rs {per_wrong:.0f}); a person handling an unsure request costs Rs {PERSON_COST} "
             f"and routes it correctly. Handling the unsure ones pays off as long as it costs less than Rs {breakeven:.0f} a request.")
    L.append("Run cost of the model: Rs 0 per prediction (no paid calls). Hosting is not priced here; it is a small program that runs on an ordinary server.\n")

    text = "\n".join(L)
    open("outputs/findings.txt", "w", encoding="utf-8").write(text)
    print(text)

    # charts
    m = tr.groupby([tr.created_at.dt.to_period("M").astype(str), "final_team"]).size().unstack(fill_value=0)
    ax = m.plot(kind="bar", stacked=True, figsize=(11, 5), colormap="tab10", width=0.85)
    ax.set_title("Requests per month by the team where they ended up")
    ax.set_xlabel(""); ax.set_ylabel("Requests")
    ax.legend(loc="center left", bbox_to_anchor=(1, 0.5), frameon=False, fontsize=8)
    plt.xticks(rotation=45, ha="right"); plt.tight_layout()
    plt.savefig("outputs/charts/monthly_by_final_team.png", dpi=150); plt.close()

    th = [0.0, 0.5, 0.6, 0.7, 0.8, 0.9]
    cov = [(v.conf >= x).mean() * 100 for x in th]
    acc = [v[v.conf >= x].ok.mean() * 100 for x in th]
    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.plot(cov, acc, marker="o")
    for x, c, a in zip(th, cov, acc):
        ax.annotate(f"{x:.1f}", (c, a), textcoords="offset points", xytext=(5, 6), fontsize=8)
    ax.axhline((tr.bot_team == tr.final_team).mean() * 100, color="grey", linestyle="--", label="Bot's own label (77%)")
    ax.set_xlabel("Share of requests routed automatically (%)"); ax.set_ylabel("Accuracy on those (%)")
    ax.set_title("Route automatically only when sure"); ax.legend()
    plt.tight_layout(); plt.savefig("outputs/charts/coverage_vs_accuracy.png", dpi=150); plt.close()
    print("\ncharts written to outputs/charts")


if __name__ == "__main__":
    run()
