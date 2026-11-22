import json
import random
import re
from pathlib import Path

from normalize import MONTHS, fold

POSTS_PATH = Path("data/processed/posts.jsonl")
ARTICLES_PATH = Path("data/processed/cleaned.jsonl")
OUT_PATH = Path("data/processed/posts_injected.jsonl")
SEED = 42
# share of clean test posts (gemini with the fact rule) that get one changed fact
INJECT_SHARE = 1 / 3
VOWELS = "aeiou"

# a digit run that is not part of a word, hashtag or code like COVID-19
DIGITS = re.compile(r"(?<![\w#-])\d+(?![\w-])")
# a capitalised word that is not the first word of a sentence
NAME = re.compile(r"(?<=[^\s.!?\n#@]\s)[A-ZČĆŠŽĐ][a-zčćšžđ]{3,}")


def digit_candidates(text):
    return [m for m in DIGITS.finditer(text)]


def name_candidates(text, article_text):
    # only words that also appear in the article, so they are real names
    return [
        m
        for m in NAME.finditer(text)
        if fold(m.group()) not in MONTHS and m.group() in article_text
    ]


def change_number(old, rng):
    n = int(old)
    if len(old) == 4 and 1900 <= n <= 2100:
        new = n + rng.choice([-2, -1, 1, 2])
    elif n <= 31:
        new = n + rng.choice([-3, -2, -1, 1, 2, 3])
        if new < 1:
            new = n + 3
    else:
        new = n + rng.choice([-1, 1]) * max(1, round(n * rng.uniform(0.1, 0.5)))
    return str(new)


def change_name(old, rng):
    positions = [i for i, c in enumerate(old) if i > 0 and c in VOWELS]
    if not positions:
        return None
    i = rng.choice(positions)
    return old[:i] + rng.choice([v for v in VOWELS if v != old[i]]) + old[i + 1 :]


def inject(post, article_text, rng):
    options = []
    if digit_candidates(post["text"]):
        options.append("number")
    if name_candidates(post["text"], article_text):
        options.append("name")
    if not options:
        return None

    kind = rng.choice(options)
    if kind == "number":
        m = rng.choice(digit_candidates(post["text"]))
        new = change_number(m.group(), rng)
    else:
        m = rng.choice(name_candidates(post["text"], article_text))
        new = change_name(m.group(), rng)
    if new is None:
        return None

    text = post["text"][: m.start()] + new + post["text"][m.end() :]
    change = {
        "kind": kind,
        "old": m.group(),
        "new": new,
        "start": m.start(),
        "end": m.start() + len(new),
    }
    return {
        **post,
        "id": post["id"] + "__inj",
        "source_id": post["id"],
        "injected": True,
        "text": text,
        "change": change,
    }


def main():
    with ARTICLES_PATH.open("r", encoding="utf-8") as f:
        articles = {a["slug"]: a["content"] for a in map(json.loads, f)}
    with POSTS_PATH.open("r", encoding="utf-8") as f:
        posts = [json.loads(line) for line in f]

    clean = sorted(
        (
            p
            for p in posts
            if p["split"] == "test"
            and p["model"] == "gemini"
            and p["prompt"] == "fact_rule"
        ),
        key=lambda p: p["id"],
    )
    rng = random.Random(SEED)
    chosen = rng.sample(clean, round(len(clean) * INJECT_SHARE))

    injected = []
    for post in sorted(chosen, key=lambda p: p["id"]):
        result = inject(post, articles[post["slug"]], rng)
        if result:
            injected.append(result)

    with OUT_PATH.open("w", encoding="utf-8") as f:
        for post in injected:
            f.write(json.dumps(post, ensure_ascii=False) + "\n")
    print(f"saved {len(injected)} posts with one changed fact to {OUT_PATH}")


if __name__ == "__main__":
    main()
