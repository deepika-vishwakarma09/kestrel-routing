"""Text cleaning shared by training and the live service (they must match exactly)."""
import re
import unicodedata


def fix_mojibake(s: str) -> str:
    """Legacy Zoho text came across with broken characters (UTF-8 read as cp1252, sometimes twice)."""
    s = str(s)
    for _ in range(2):
        try:
            fixed = s.encode("cp1252").decode("utf-8")
        except (UnicodeEncodeError, UnicodeDecodeError):
            break
        if fixed == s:
            break
        s = fixed
    return s


def clean_text(s: str) -> str:
    s = fix_mojibake(s)
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode("ascii")  # accents and symbols out
    s = s.lower()
    s = re.sub(r"\bsr\d+\b", " ", s)          # request / registration numbers carry no meaning
    s = re.sub(r"\d+", " ", s)                # other numbers: keep the model from memorising ids
    s = re.sub(r"[^a-z&' ]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


# Some requests raise two things ("installation slot not confirmed, box was open and scratched").
# In the past data the request usually ended with the team for the LAST thing mentioned, so the
# last clause is given to the model as its own feature (it lifted two-part requests from 76% to 91%).
_FILLER = (r"\b(thanks|thank you|asap|very disappointed|kindly resolve|pls call back|please call back|pls help|urgent|"
           r"good morning|namaste|hello team|hi|sir|reg no sr\d+|order ko\d+)\b")


def clauses(raw: str):
    s = fix_mojibake(raw).lower()
    s = re.sub(r"reg no sr\d+|order ko\d+", "", s)
    parts = [p.strip() for p in s.split(",") if p.strip()]
    out = [clean_text(re.sub(_FILLER, "", p)) for p in parts]
    return [p for p in out if p]


def last_clause(raw: str) -> str:
    c = clauses(raw)
    return c[-1] if c else ""
