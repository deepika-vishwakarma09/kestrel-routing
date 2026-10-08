# Handoff: the three things Monday's person must know

1. **Run it.** Put the five Kestrel CSVs in `data/raw/` (`train.csv`, `test_unlabelled.csv`, `teams.csv`, `resolution_log.csv`, `sample_submission.csv`), then `python run.py`. It cleans, trains, tests, writes `predictions.csv` and the cost figures in about a minute. The data is not in the repo because it is customer data (policy section 10). To use the service: `uvicorn service.app:app --port 8000`, then open http://localhost:8000. The trained model is saved in `models/router.joblib`, so the service starts without the data and without any key. If that file is missing it starts anyway and tells you what to run.
2. **The target is where a request ended up (`final_team`), not the bot's label, and the test is by time.** Do not switch back to the bot's label, and do not test on a random split: the real requests come after the training ones. `python -m src.evaluate` runs the time-based tests. Retrain from time to time and re-check accuracy against the final teams of recent requests.
3. **Check these before relying on the rupees or the headcount.** (a) The cost of a person handling an unsure request (Rs 260) is my assumption. (b) There is no staffing data, so the team figures are demand, not load per person. (c) `final_team` is treated as the right answer, but about 1 request in 80 looks wrongly closed. (d) Run the model next to the bot for two weeks before switching the bot off.

## Known bugs and shortcuts
- No labels exist for the Jul to Sep 2026 test months, so the expected score (85.5%) assumes they look like earlier months.
- The model is overconfident on some vague messages (for example 0.66 on "complaint about product asap"). Auto-routing only above 0.7 reduces this but does not remove it.
- The "last part decides" rule is a pattern found in past data. It only splits on commas.
- All text is reduced to plain English letters. Non-English scripts would be dropped, and the request would be sent to a person.
- The saved model must be loaded with a compatible scikit-learn version. If loading fails, run `python -m src.train` with the data in place.
- Predictions use the seven team names in the `team` column of `teams.csv` (Installations, Consumables). If the scorer expects the renamed names, map them with the `renamed_to` column.
- The service has no login, no logging and handles one request at a time. It is a demo, not a production deployment.
- The review of 98 mistakes was typed by hand from my reading, and a second reader may group some differently. There are no automated tests.
