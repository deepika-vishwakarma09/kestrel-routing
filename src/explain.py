"""Reasons a Kestrel employee can read for each routing decision.

Used by predict.py and by the service. No API or key needed.
"""
import joblib
import numpy as np
import pandas as pd

from src.text import clauses, clean_text, last_clause

MODEL_PATH = "models/router.joblib"
AUTO_ROUTE_AT = 0.70      # at or above this confidence the request is routed automatically (98.0% right in backtests)
VAGUE_BELOW = 0.50        # below this the message usually does not say what the problem is (17.6% right in backtests)
# small words that carry no meaning on their own; they are skipped when listing reasons
STOP = {"up", "but", "of", "the", "a", "an", "my", "is", "to", "and", "pls", "please", "about", "with", "in", "on",
        "at", "it", "i", "me", "we", "for", "this", "that", "sir", "hi", "hello", "very", "asap", "kindly", "thanks"}
PAY_WORDS = ("paid", "payment", "pay ", "charged", "paying")
JOB_WORDS = ("install", "demo", "repair", "technician", "visit", "service")

_model = None


def get_model():
    global _model
    if _model is None:
        _model = joblib.load(MODEL_PATH)
    return _model


def _frame(rec):
    return pd.DataFrame([{
        "text": clean_text(rec.get("request_text", "")),
        "last_clause": last_clause(rec.get("request_text", "")),
    }])


def explain(rec, top_k=4):
    """rec: dict with request_text. Other fields are accepted and ignored. Returns a dict."""
    model = get_model()
    df = _frame(rec)
    pre, clf = model[0], model[1]
    X = pre.transform(df)
    proba = clf.predict_proba(X)[0]
    order = np.argsort(proba)[::-1]
    team = str(clf.classes_[order[0]])
    conf = float(proba[order[0]])

    # which words / fields pushed towards the chosen team
    names = pre.get_feature_names_out()
    contrib = X.toarray()[0] * clf.coef_[order[0]]
    idx = np.argsort(contrib)[::-1][:top_k + 2]
    words = []
    for i in idx:
        if contrib[i] <= 0.05:
            continue
        w = names[i].split("__", 1)[1]
        toks = w.split()
        if all(t in STOP for t in toks) or toks[0] in STOP or toks[-1] in STOP:
            continue
        if w not in words and not any(w in other or other in w for other in words):
            words.append(w)
    words = words[:top_k]

    reasons = []
    if words:
        reasons.append("Words in the message that point to " + team + ": " + ", ".join(f'"{w}"' for w in words) + ".")

    parts = [c for c in clauses(rec.get("request_text", "")) if len(c.split()) >= 3]
    if len(parts) > 1:
        reasons.append(f'The message raises more than one thing. In past requests the case usually ended with the team for the '
                       f'last thing mentioned, so "{parts[-1]}" was weighted.')
    t = df.text[0]
    if team != "Billing" and any(w in t + " " for w in PAY_WORDS) and any(w in t for w in JOB_WORDS):
        reasons.append("The customer mentions paying, but the problem is the job itself (installation, repair or service). "
                       "Under policy section 3 this is not a Billing request.")
    if conf < VAGUE_BELOW:
        reasons.append("The message does not say clearly what the problem is. Models and people both get this kind of "
                       "request wrong more than 4 times in 5, so a person should read it or ask the customer.")
    elif conf < AUTO_ROUTE_AT:
        reasons.append("The message is only partly clear, so this is a suggestion for a person to confirm.")

    action = "route_automatically" if conf >= AUTO_ROUTE_AT else "send_to_person"
    return {
        "team": team,
        "confidence": round(conf, 3),
        "action": action,
        "alternatives": [{"team": str(clf.classes_[j]), "probability": round(float(proba[j]), 3)} for j in order[1:3]],
        "reasons": reasons,
    }
