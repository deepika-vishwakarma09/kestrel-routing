# Expected score (written before submitting predictions.csv)

**Metric:** accuracy, the share of test requests sent to the team where they actually ended up (`final_team`). I chose it because that is what the business pays for: each wrong destination costs Rs 305 per transfer plus an extra contact (Rs 260).

**Expected: 85.5%**, most likely between 84.3% and 87.0% (the 95% range from the backtests, widened by half a point for drift).

## How I estimated it

1. Backtests: trained only on earlier requests and tested on the next 3 months, 3 times (6,502 requests). Plain accuracy 85.6%.
2. The test set has a different mix of clear and vague messages, so I weighted the backtest accuracy of each confidence band by how many test requests fall in that band:

| Confidence band | Share of test requests | Accuracy in backtests |
|---|---|---|
| under 0.5 | 13.5% | 17.2% |
| 0.5 to 0.7 | 2.3% | 26.2% |
| 0.7 to 0.9 | 2.9% | 86.9% |
| 0.9 or more | 81.3% | 98.5% |

Test requests the model would route automatically (confidence 0.7 or more): 84.2%.

## What could make the real score lower

- The test months (Jul to Sep 2026) are all after the CRM switch and I have no labels to check drift.
- The model is overconfident when it is unsure: in the 0.5 to 0.7 band it averages 58% confidence but is right 26% of the time. So I did not use its own confidence as the estimate.
- If the hidden outcome is the bot's queue rather than the final team, expect about 80%.
- About 1.2% of requests (1 in 80) end up somewhere the model was very sure was wrong, so those cannot be fixed by a better model.
