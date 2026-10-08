"""Step 2: the routing model.

TF-IDF on the cleaned request text plus a second TF-IDF on its last clause, then logistic regression.
Text only: channel, product family and warranty status added nothing (85.6% without them vs 85.5% with), and the
product family column names a different product from the message in 17.5% of requests, so it is not trusted.
Target is `final_team` (where the request really ended up), NOT the bot's label (see docs/decisions.md #1).
Words must appear in at least 5 requests to enter the vocabulary, so the saved model holds no rare words
(ops-policy section 10: customer data must not be published).

Run:  python -m src.train
"""
import json
import os

import joblib
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline

CLEAN = "data/clean"
MODEL_PATH = "models/router.joblib"
TARGET = "final_team"


def build_model():
    features = ColumnTransformer([
        ("words", TfidfVectorizer(ngram_range=(1, 2), min_df=5, sublinear_tf=True), "text"),
        ("last", TfidfVectorizer(ngram_range=(1, 2), min_df=5, sublinear_tf=True), "last_clause"),
    ])
    return make_pipeline(features, LogisticRegression(max_iter=3000, C=5))


def load_train():
    return pd.read_csv(f"{CLEAN}/train_clean.csv", parse_dates=["created_at"])


def run():
    os.makedirs("models", exist_ok=True)
    tr = load_train()
    model = build_model().fit(tr, tr[TARGET])
    joblib.dump(model, MODEL_PATH)
    card = {"trained_on_rows": len(tr), "from": str(tr.created_at.min()), "to": str(tr.created_at.max()),
            "target": TARGET, "classes": list(model.classes_)}
    json.dump(card, open("models/model_card.json", "w"), indent=2)
    vocab = len(model[0].named_transformers_["words"].vocabulary_)
    print(f"trained on {len(tr)} requests, {vocab} words in vocabulary, saved to {MODEL_PATH}")
    return model


if __name__ == "__main__":
    run()
