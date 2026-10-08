"""Step 1: clean the raw exports and write data/clean/train_clean.csv and test_clean.csv."""
import os

import pandas as pd

from src.text import clean_text, last_clause

RAW, CLEAN = "data/raw", "data/clean"
IST_OFFSET = pd.Timedelta(hours=5, minutes=30)
# Two teams were renamed on 15 Jan 2026 (ops-policy section 5; responsibilities unchanged).
# Canonical names are the seven in teams.csv, the `team` column.
CANON = {"Installs & Demo": "Installations", "Filters & Consumables": "Consumables"}
VAL_START = "2026-04-01"   # validate on the last 3 months of train, like the test set follows train


def run():
    os.makedirs(CLEAN, exist_ok=True)
    tr = pd.read_csv(f"{RAW}/train.csv")
    te = pd.read_csv(f"{RAW}/test_unlabelled.csv")
    rl = pd.read_csv(f"{RAW}/resolution_log.csv")
    log = {"train_rows": len(tr), "test_rows": len(te)}

    tr = tr.merge(rl, on="request_id", how="left", validate="1:1")
    for c in ["team_label", "first_team", "final_team"]:
        tr[c] = tr[c].replace(CANON)
    tr = tr.rename(columns={"team_label": "bot_team", "final_team": "final_team"})

    # Zoho resolution events are UTC and were never converted (policy section 9)
    tr["created_at"] = pd.to_datetime(tr["created_at_ist"])
    tr["resolved_at"] = pd.to_datetime(tr["resolved_at"])
    legacy = tr["source"] == "legacy_zoho"
    log["negative_resolution_before_fix"] = int(((tr.resolved_at - tr.created_at).dt.total_seconds() < 0).sum())
    tr.loc[legacy, "resolved_at"] = tr.loc[legacy, "resolved_at"] + IST_OFFSET
    tr["resolution_hours"] = (tr.resolved_at - tr.created_at).dt.total_seconds() / 3600
    log["negative_resolution_after_fix"] = int((tr.resolution_hours < 0).sum())

    for df in (tr, te):
        df["text"] = df["request_text"].map(clean_text)
        df["last_clause"] = df["request_text"].map(last_clause)
    te["created_at"] = pd.to_datetime(te["created_at_ist"])
    tr["split"] = (tr.created_at >= VAL_START).map({False: "fit", True: "val"})
    log["fit_rows"] = int((tr.split == "fit").sum())
    log["val_rows"] = int((tr.split == "val").sum())
    log["empty_text_after_clean"] = int((tr.text == "").sum() + (te.text == "").sum())
    log["duplicate_request_ids"] = int(tr.request_id.duplicated().sum() + te.request_id.duplicated().sum())

    tr.to_csv(f"{CLEAN}/train_clean.csv", index=False)
    te.to_csv(f"{CLEAN}/test_clean.csv", index=False)
    for k, v in log.items():
        print(f"  {k}: {v}")
    return tr, te


if __name__ == "__main__":
    run()
