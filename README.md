# Kestrel Home: service-request routing

A small model that reads a customer's request and says which of Kestrel's seven teams should get it, how sure it is, and why. It replaces the routing bot (Rs 3.2 lakh a year) and costs Rs 0 per request: it makes no paid calls and needs no API key.

**Main finding:** the bot's labels are not the right answer. They show where the bot sent a request, and only 77.2% of those match the team that finally closed it. A model trained to copy the bot reaches the 90% asked for in the brief (96.6%) but is right only 78.7% of the time. So I trained on where requests actually ended up. That model is right 85.6% of the time, and is very sure (98.1% right) on 84.3% of requests. The rest go to a person. Full reasoning in [`docs/memo.md`](docs/memo.md).

**Screen recording (3 min):** [RECORDING LINK]

## Run the service (30 seconds, no data and no key needed)

Needs Python 3.10 or newer. The trained model is saved in `models/router.joblib`.

```bash
git clone https://github.com/deepika-vishwakarma09/kestrel-routing.git
cd kestrel-routing
python -m venv venv
.\venv\Scripts\Activate.ps1          # Mac/Linux: source venv/bin/activate
pip install -r requirements.txt
uvicorn service.app:app --port 8000
```

Open **http://localhost:8000**. Paste a customer message, or press one of the four example buttons. The screen shows the team, the confidence, whether to route automatically or send to a person, and the reasons.

If the model file is missing the service still starts, and says what to run.

### The endpoint

`POST /route` takes one request as JSON and returns the team and the reasons.

```bash
curl -X POST http://localhost:8000/route -H "Content-Type: application/json" \
  -d '{"request_text": "hello, paid for installation of my water purifier but nobody turned up"}'
```
```json
{
  "team": "Installations",
  "confidence": 0.976,
  "action": "route_automatically",
  "alternatives": [{"team": "Repairs", "probability": 0.007}, {"team": "Billing", "probability": 0.007}],
  "reasons": [
    "Words in the message that point to Installations: \"installation\".",
    "The customer mentions paying, but the problem is the job itself (installation, repair or service). Under policy section 3 this is not a Billing request."
  ]
}
```

`action` is `route_automatically` when the confidence is 0.70 or more (98.1% right in the tests) and `send_to_person` below that. Only `request_text` is needed. Other fields are accepted and ignored. An empty message returns a clear 422 error. `GET /health` says whether the model is loaded.

## Re-run everything from the data

The five Kestrel files are not in this repo because they hold customer data (ops-policy section 10). Create `data/raw/` if it does not exist and put these in it:
`train.csv`, `test_unlabelled.csv`, `teams.csv`, `resolution_log.csv`, `sample_submission.csv`

```bash
python run.py
```

It takes about a minute and runs five steps: clean, train, test, predict, cost. Expected output includes:
```
negative_resolution_after_fix: 0
All folds ... 85.6% (84.8% to 86.5%)
format check passed: 2178 rows, one per request_id, all teams valid
Saving per year: model routes everything Rs 8.3 lakh; model plus person for the unsure ones Rs 12.6 lakh.
```
It writes `predictions.csv` (the file to score), `docs/expected_score.md`, `outputs/findings.txt`, `outputs/charts/` and `eval/report.md`.

## How I know it works

Time-based tests: the model is trained only on earlier requests and tested on the next three months, three times, on 6,502 requests. A random split would flatter it, because the real test requests come after the training ones.

| | Bot's own label | Model |
|---|---|---|
| Right team, all three tests | 77.2% (76.2% to 78.2%) | **85.6%** (84.8% to 86.5%) |
| Each test | 77.5%, 77.5%, 76.7% | 85.0%, 86.2%, 85.8% |

| Trained on | Matches the bot's label | Reaches the real destination |
|---|---|---|
| The bot's labels (what the brief asked for) | 96.6% | 78.7% |
| Where requests ended up | 79.7% | **85.6%** |

**Expected score on the held-back requests: 85.5%**, most likely between 84.3% and 87.0%, written before predictions were submitted in [`docs/expected_score.md`](docs/expected_score.md).

**When it is wrong:** I looked at all 934 mistakes. About 84% are messages that name a product but not the problem ("not happy with water purifier"), so no model can route them; 8% are clear messages that ended up somewhere that contradicts them; 8% are two-part messages. On this data nothing reading only the message gets much above 88% to 89%, so the 90% in the brief is out of reach unless a person asks the customer. See [`eval/error_review_summary.md`](eval/error_review_summary.md).

## What I changed along the way

- Trained on `final_team` instead of the bot's label (96.6% vs 78.7% on the real destination).
- Added the last part of the message as its own feature. When a message raises two things, the request usually ends with the team for the last one. This raised accuracy from 83.8% to 85.5%, with the same gain in all three tests.
- Dropped channel, product and warranty. They added nothing, and the product column names a different product from the message in 17.5% of requests.
- Dropped character-based text features. They did not help and store more customer text.

## The rupees

A wrong routing costs Rs 698 (1.44 transfers at Rs 305, plus Rs 260 for the extra contact; ops-policy section 4). At about 726 requests a month the bot's wrong routings cost Rs 1.16 lakh a month, on top of the Rs 3.2 lakh licence.

| Option | Saving a year vs the bot |
|---|---|
| Model routes everything | Rs 8.3 lakh |
| Model routes when sure, a person reads the rest (about 114 a month) | Rs 12.6 lakh |

The second row assumes a person handling an unsure request costs Rs 260 and routes it correctly. It pays off as long as it costs less than Rs 568. Busiest teams (requests a month by where they end up): Repairs 169, Installations 106, Returns 103, Product Advice 93, Warranty 92, Billing 88, Consumables 71.

## Project structure

```
kestrel-routing/
├── README.md
├── run.py                  one command: clean, train, test, predict, cost
├── predictions.csv         the file to score (2,178 rows: request_id, team)
├── requirements.txt
│
├── src/
│   ├── text.py             cleaning the message text (shared with the service)
│   ├── clean.py            step 1: merge team names, fix Zoho times and text
│   ├── train.py            step 2: the model (TF-IDF + logistic regression)
│   ├── evaluate.py         step 3: time-based tests, confidence, error types
│   ├── explain.py          the reasons shown to an employee
│   ├── predict.py          step 4: predictions.csv, format check, expected score
│   └── business.py         step 5: rupees and busiest teams
│
├── service/
│   ├── app.py              the endpoint
│   └── static/index.html   the screen
│
├── models/                 router.joblib: the trained model (1,688 common words, no customer text)
├── eval/                   report.md, confusion_matrix.csv, error_review.csv, error_review_summary.md
├── outputs/                findings.txt and charts/
├── docs/                   memo, decisions, expected_score, handoff_notes, ai_usage_log
└── data/                   NOT in the repo: you add the five CSVs to data/raw/
```

## Limits

- No labels exist for the Jul to Sep 2026 test months, so the expected score assumes they look like earlier months.
- The model uses only the words in the message. Non-English scripts are dropped, and that request goes to a person.
- The service is a demo: no login, no logging, one request at a time.
- There is no staffing file in the Kestrel pack, so the team figures show demand, not load per person.

## Read next

- [`docs/memo.md`](docs/memo.md): the one-page memo to Ritu Deshpande
- [`docs/decisions.md`](docs/decisions.md): what was unclear, what I decided and why
- [`docs/handoff_notes.md`](docs/handoff_notes.md): what to know before taking this over
- [`docs/ai_usage_log.md`](docs/ai_usage_log.md): how I used AI
