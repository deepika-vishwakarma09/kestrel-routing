# Evidence report

Time-based backtests on 6,502 requests (3 folds, each trained only on earlier requests). Target: `final_team`.

## 1. Accuracy against where requests really ended up

| Fold (test window) | Requests | Bot's own label | Model | Model macro-F1 |
|---|---|---|---|---|
| 2025-10-01 to 2026-01-01 | 2,199 | 77.5% | 85.0% | 0.848 |
| 2026-01-01 to 2026-04-01 | 2,168 | 77.5% | 86.2% | 0.861 |
| 2026-04-01 to 2026-07-01 | 2,135 | 76.7% | 85.8% | 0.856 |
| **All folds** | **6,502** | **77.2%** (76.2% to 78.2%) | **85.6%** (84.8% to 86.5%) | 0.855 |

## 2. The 90% target in the brief: matching the bot's labels

| Model trained on | Matches the bot's label | Reaches the real destination |
|---|---|---|
| The bot's labels (what the brief asked for) | 96.6% | 78.7% |
| Where requests ended up (`final_team`) | 79.7% | 85.6% |

## 3. Confidence: when to trust it

| Auto-route only when confidence is at least | Requests auto-routed | Accuracy on those | Left for a person |
|---|---|---|---|
| 0.0 | 100.0% | 85.6% | 0.0% |
| 0.5 | 86.8% | 96.0% | 13.2% |
| 0.6 | 85.2% | 97.5% | 14.8% |
| 0.7 | 84.3% | 98.1% | 15.7% |
| 0.8 | 83.8% | 98.4% | 16.2% |
| 0.9 | 81.7% | 98.5% | 18.3% |

| Confidence band | Requests | Accuracy | Mean confidence |
|---|---|---|---|
| (0.0, 0.5] | 857 | 17.2% | 34.1% |
| (0.5, 0.7] | 164 | 26.2% | 58.3% |
| (0.7, 0.9] | 168 | 86.9% | 84.7% |
| (0.9, 1.0] | 5,313 | 98.5% | 97.8% |

## 4. How it gets it wrong

| Kind of error | Count | Share of all errors |
|---|---|---|
| Vague message, model unsure (confidence under 0.5) | 710 | 76% |
| Partly clear, model fairly unsure (0.5 to 0.9) | 143 | 15% |
| Model very sure (0.9 or more) but the destination differs | 81 | 9% |

Per team, share of requests sent to the right team:

| Team | Requests | Recall |
|---|---|---|
| Billing | 808 | 86.3% |
| Consumables | 643 | 82.6% |
| Installations | 972 | 83.7% |
| Product Advice | 828 | 85.0% |
| Repairs | 1,508 | 90.4% |
| Returns & Replacement | 941 | 84.0% |
| Warranty Claims | 802 | 83.4% |
