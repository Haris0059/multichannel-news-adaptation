import json
import random
import re
from pathlib import Path

IN_PATH = Path("data/processed/cleaned.jsonl")
SPLIT_PATH = Path("data/split.json")
OUT_DIR = Path("data/processed/agreement")
SENTENCES_PATH = OUT_DIR / "sentences.jsonl"
TASKS_PATH = OUT_DIR / "label_studio_tasks.json"
SEED = 42
N_SENTENCES = 50
MIN_WORDS = 8
MAX_WORDS = 60
# random sentences rarely hold dates and numbers, so half the sample needs a digit
N_WITH_DIGIT = 25

# a period after these words does not end a sentence ("Prof. Dr. Amra Hodžić")
ABBREVIATIONS = {"prof", "dr", "assoc", "asst", "mr", "mrs", "ms", "no", "st", "vs"}
SENTENCE_END = re.compile(r"(?<=[.!?])\s+(?=[\"“‘(]?[A-Z0-9ČĆŠŽĐ])")


def split_sentences(text):
    sentences = []
    for paragraph in text.splitlines():
        start = 0
        for m in SENTENCE_END.finditer(paragraph):
            last_word = paragraph[start : m.start()].split()[-1]
            # skip abbreviations and initials like "A."
            if last_word.rstrip(".").lower() in ABBREVIATIONS or len(last_word) <= 2:
                continue
            sentences.append(paragraph[start : m.start()])
            start = m.end()
        sentences.append(paragraph[start:])
    return [s.strip() for s in sentences if s.strip()]


def main():
    with SPLIT_PATH.open("r", encoding="utf-8") as f:
        train = set(json.load(f)["train"])

    with IN_PATH.open("r", encoding="utf-8") as f:
        articles = [json.loads(line) for line in f]
    articles = sorted(
        (a for a in articles if a["slug"] in train), key=lambda a: a["slug"]
    )

    # one sentence per article, so no single article dominates the sample
    rng = random.Random(SEED)
    rng.shuffle(articles)
    sample = []
    for article in articles:
        sentences = split_sentences(article["content"])
        candidates = [
            (i, s)
            for i, s in enumerate(sentences)
            if MIN_WORDS <= len(s.split()) <= MAX_WORDS
        ]
        if len(sample) < N_WITH_DIGIT:
            candidates = [(i, s) for i, s in candidates if re.search(r"\d", s)]
        if not candidates:
            continue
        i, text = rng.choice(candidates)
        sample.append(
            {"id": f"{article['slug']}#{i}", "slug": article["slug"], "text": text}
        )
        if len(sample) == N_SENTENCES:
            break

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with SENTENCES_PATH.open("w", encoding="utf-8") as f:
        for record in sample:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    tasks = [{"data": {"id": r["id"], "text": r["text"]}} for r in sample]
    with TASKS_PATH.open("w", encoding="utf-8") as f:
        json.dump(tasks, f, ensure_ascii=False, indent=2)

    print(f"saved {len(sample)} sentences to {SENTENCES_PATH} and {TASKS_PATH}")


if __name__ == "__main__":
    main()
