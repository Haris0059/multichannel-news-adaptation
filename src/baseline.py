import json
import re
from pathlib import Path

from compare import compare_facts
from normalize import MONTHS, NUMBER_WORDS, fold

ARTICLES_PATH = Path("data/processed/cleaned.jsonl")
POSTS_PATH = Path("data/processed/posts.jsonl")
INJECTED_PATH = Path("data/processed/posts_injected.jsonl")
OUT_PATH = Path("results/predictions/baseline.jsonl")

# dates are matched on folded text (lowercase, no diacritics), so one month list
# covers English, Bosnian, Croatian and Serbian forms
MONTH = r"(?:" + "|".join(sorted(MONTHS, key=len, reverse=True)) + r")(?![a-z])\.?"
DAY = r"\d{1,2}(?:st|nd|rd|th)?\.?"
DAYS = rf"{DAY}(?:\s*[–—-]\s*{DAY})?"
YEAR = r"(?:19|20)\d{2}\.?"
DATE = re.compile(
    "|".join(
        [
            rf"\b{DAYS}\s*(?:of\s+)?{MONTH}(?:,?\s+{YEAR})?",  # 21. oktobra 2026.
            rf"\b{MONTH}\s+{DAYS}(?:,?\s+{YEAR})?",  # October 21, 2026
            rf"\b{MONTH}\s+{YEAR}",  # October 2026
            r"\b\d{1,2}\.\s?\d{1,2}\.(?:\s?\d{4}\.?)?",  # 21.10.2026.
            r"\b\d{1,2}/\d{1,2}/\d{4}\b",  # 21/10/2026
            r"\b(?:19|20)\d{2}(?:\s*/\s*(?:19|20)?\d{2})?\.?(?!\d)",  # 2026, 2026/2027
        ]
    )
)
# digits not glued to letters, hashtags, codes or times; 1.500 and 1,5 are one number
NOT_BEFORE = r"(?<![\w#:.,/-])"
DIGITS = (
    rf"{NOT_BEFORE}\d{{1,3}}(?:[.,]\d{{3}})+(?:[.,]\d+)?(?![\w:])"
    rf"|{NOT_BEFORE}\d+(?:[.,]\d+)?(?![\w:])"
)
# "sto" (100) is left out: folded "što" (what, that) is one of the most common words
WORDS = (
    r"\b(?:"
    + "|".join(w for w, v in NUMBER_WORDS.items() if v >= 2 and w != "sto")
    + r")\b"
)
NUMBER = re.compile(f"{DIGITS}|{WORDS}")

# capitalised words, joined by short connectors: "University of Sarajevo",
# "Univerzitet u Sarajevu"; "and" and "i" would join two different names, and
# only spaces join words, so a name never runs over a line break
CAP = r"[A-ZČĆŠŽĐ][\w’'-]*"
NAME = re.compile(rf"{CAP}(?:[ \t]+(?:of|for|the|u|za|na)[ \t]+{CAP}|[ \t]+{CAP})*")
TITLE_FORMS = (
    "prof dr doc mr mrs ms assoc asst academician akademik rector rektor dean dekan"
)
TITLES = set(TITLE_FORMS.split())
NOT_NAMES = {"km", "eur", "usd", "bam"}
# word starts that make a capitalised name an organisation (folded)
ORG_FORMS = (
    "universit univerzitet facult fakultet department odsjek institut ministr "
    "academ akademij associat udruzenj cent company bank school skol agenc embass "
    "ambasad council vijec office hub incubat inkubat librar bibliotek foundation "
    "fondacij"
)
ORG_WORDS = tuple(ORG_FORMS.split())
WEEKDAY_FORMS = (
    "monday tuesday wednesday thursday friday saturday sunday "
    "ponedjeljak utorak srijeda cetvrtak petak subota nedjelja"
)
WEEKDAYS = set(WEEKDAY_FORMS.split())
# a few articles are in Bosnian; the more common function words decide the language
BS_WORDS = {"je", "i", "u", "na", "za", "se", "su", "od", "koji", "koja", "da"}
EN_WORDS = {"the", "and", "of", "to", "in", "is", "for", "with", "on"}


def article_lang(text):
    words = fold(text).split()
    bosnian = sum(w in BS_WORDS for w in words)
    english = sum(w in EN_WORDS for w in words)
    return "bs" if bosnian > english else "en"


def overlaps(span, spans):
    return any(span["start"] < s["end"] and s["start"] < span["end"] for s in spans)


def name_type(words, sentence_start):
    folded = [fold(w) for w in words]
    if len(words) == 1 and folded[0] in NOT_NAMES:
        return None
    if any(w.startswith(ORG_WORDS) for w in folded) or any(
        len(w) >= 2 and w.isupper() for w in words
    ):
        return "ORG"
    if len(words) == 1 and (
        sentence_start or folded[0] in MONTHS or folded[0] in WEEKDAYS
    ):
        return None
    return "PERSON"


def extract(text):
    folded = fold(text)
    facts = []
    for m in DATE.finditer(folded):
        facts.append(
            {
                "text": text[m.start() : m.end()],
                "type": "DATE",
                "start": m.start(),
                "end": m.end(),
            }
        )
    for m in NUMBER.finditer(folded):
        span = {
            "text": text[m.start() : m.end()],
            "type": "NUMBER",
            "start": m.start(),
            "end": m.end(),
        }
        if not overlaps(span, facts):
            facts.append(span)

    for m in NAME.finditer(text):
        start = m.start()
        if start and text[start - 1] in "#@":
            continue
        words = m.group().split()
        # titles are not part of the name (labelling rules, PERSON)
        while words and fold(words[0]).rstrip(".") in TITLES:
            start = text.index(words[1], start) if len(words) > 1 else m.end()
            words = words[1:]
        # a single letter ("U", "A") is a word, not a name
        if not words or (len(words) == 1 and len(words[0]) < 2):
            continue
        # after punctuation, an emoji, ** or a line break a capital letter starts a
        # sentence; only a letter, digit or comma before it means mid-sentence
        before = text[:start].rstrip()
        sentence_start = not before or not (before[-1].isalnum() or before[-1] == ",")
        fact_type = name_type(words, sentence_start)
        span = {
            "text": text[start : m.end()],
            "type": fact_type,
            "start": start,
            "end": m.end(),
        }
        if fact_type and not overlaps(span, facts):
            facts.append(span)
    return sorted(facts, key=lambda f: f["start"])


def main():
    with ARTICLES_PATH.open("r", encoding="utf-8") as f:
        articles = {
            a["slug"]: f"{a['title']}\n\n{a['content']}" for a in map(json.loads, f)
        }
    with POSTS_PATH.open("r", encoding="utf-8") as f:
        posts = [p for p in map(json.loads, f) if p["split"] == "test"]
    if INJECTED_PATH.exists():
        with INJECTED_PATH.open("r", encoding="utf-8") as f:
            posts += [json.loads(line) for line in f]

    source_facts = {}
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUT_PATH.open("w", encoding="utf-8") as f:
        for post in posts:
            slug = post["slug"]
            if slug not in source_facts:
                text = articles[slug]
                source_facts[slug] = (extract(text), article_lang(text))
            facts, source_lang = source_facts[slug]
            results = compare_facts(
                facts, extract(post["text"]), post["lang"], source_lang
            )
            spans = [
                {k: r[k] for k in ("start", "end", "text", "type", "label", "source")}
                for r in results
            ]
            f.write(
                json.dumps({"id": post["id"], "spans": spans}, ensure_ascii=False)
                + "\n"
            )
    print(f"saved baseline predictions for {len(posts)} posts to {OUT_PATH}")


if __name__ == "__main__":
    main()
