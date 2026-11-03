import csv
import json
import re
from itertools import combinations
from pathlib import Path

AGREEMENT_DIR = Path("data/processed/agreement")
SENTENCES_PATH = AGREEMENT_DIR / "sentences.jsonl"
HUMAN_DIR = AGREEMENT_DIR / "human"
LLM_DIR = AGREEMENT_DIR / "llm"
GOLD_NAME = "gold"
KAPPA_PATH = Path("results/agreement_kappa.csv")
SCORES_PATH = Path("results/annotator_scores.csv")
LABELS = ["PERSON", "ORG", "DATE", "NUMBER"]
# ignored at span edges, so "21." and "21" count as the same span
EDGE_CHARS = " .,;:!?\"'()“”‘’"
WORD = re.compile(r"\w+")


def load_label_studio(path):
    """Read a Label Studio JSON export: one annotation per task, keyed by sentence id."""
    with path.open("r", encoding="utf-8") as f:
        tasks = json.load(f)
    labelled = {}
    for task in tasks:
        if not task.get("annotations"):
            continue
        result = task["annotations"][0]["result"]
        labelled[task["data"]["id"]] = [
            {
                "text": r["value"]["text"],
                "type": r["value"]["labels"][0],
                "start": r["value"]["start"],
                "end": r["value"]["end"],
            }
            for r in result
            if r["type"] == "labels"
        ]
    return labelled


def load_llm(path):
    with path.open("r", encoding="utf-8") as f:
        records = [json.loads(line) for line in f]
    return records[0]["model"], {r["id"]: r["spans"] for r in records}


def trim(span, text):
    start, end = span["start"], span["end"]
    while start < end and text[start] in EDGE_CHARS:
        start += 1
    while end > start and text[end - 1] in EDGE_CHARS:
        end -= 1
    return start, end, span["type"]


def token_tags(spans, text):
    """One tag per word: the type of the span it falls in, or O."""
    tags = []
    for m in WORD.finditer(text):
        tag = "O"
        for s in spans:
            if s["start"] < m.end() and m.start() < s["end"]:
                tag = s["type"]
        tags.append(tag)
    return tags


def cohen_kappa(a, b):
    n = len(a)
    observed = sum(x == y for x, y in zip(a, b)) / n
    expected = sum((a.count(c) / n) * (b.count(c) / n) for c in set(a) | set(b))
    if expected == 1:
        return 1.0
    return (observed - expected) / (1 - expected)


def prf(gold, pred):
    tp = len(gold & pred)
    p = tp / len(pred) if pred else 0.0
    r = tp / len(gold) if gold else 0.0
    f1 = 2 * p * r / (p + r) if p + r else 0.0
    return p, r, f1


def span_set(labelled, texts, ids, label=None):
    return {
        (i, *trim(s, texts[i]))
        for i in ids
        for s in labelled.get(i, [])
        if label is None or s["type"] == label
    }


def main():
    with SENTENCES_PATH.open("r", encoding="utf-8") as f:
        texts = {r["id"]: r["text"] for r in map(json.loads, f)}

    annotators = {
        p.stem: load_label_studio(p) for p in sorted(HUMAN_DIR.glob("*.json"))
    }
    for path in sorted(LLM_DIR.glob("*.jsonl")):
        model, labelled = load_llm(path)
        annotators[model] = labelled
    gold = annotators.pop(GOLD_NAME, None)

    KAPPA_PATH.parent.mkdir(parents=True, exist_ok=True)
    with KAPPA_PATH.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["annotator_a", "annotator_b", "sentences", "tokens", "kappa"])
        print("\npairwise token-level Cohen's kappa")
        for a, b in combinations(annotators, 2):
            ids = sorted(set(annotators[a]) & set(annotators[b]))
            tags_a, tags_b = [], []
            for i in ids:
                tags_a += token_tags(annotators[a][i], texts[i])
                tags_b += token_tags(annotators[b][i], texts[i])
            if not tags_a:
                continue
            kappa = cohen_kappa(tags_a, tags_b)
            writer.writerow([a, b, len(ids), len(tags_a), f"{kappa:.3f}"])
            print(f"  {a} vs {b}: {kappa:.3f} ({len(ids)} sentences)")
    print(f"saved kappa to {KAPPA_PATH}")

    if gold is None:
        print(f"no {HUMAN_DIR / GOLD_NAME}.json yet, skipping scores against gold")
        return

    with SCORES_PATH.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["annotator", "type", "precision", "recall", "f1"])
        print("\nspan F1 against gold (exact match after trimming punctuation)")
        for name, labelled in annotators.items():
            ids = sorted(set(gold) & set(labelled))
            line = []
            for label in LABELS + [None]:
                p, r, f1 = prf(
                    span_set(gold, texts, ids, label),
                    span_set(labelled, texts, ids, label),
                )
                writer.writerow(
                    [name, label or "ALL", f"{p:.3f}", f"{r:.3f}", f"{f1:.3f}"]
                )
                line.append(f"{label or 'ALL'} {f1:.2f}")
            print(f"  {name}: " + "  ".join(line))
    print(f"saved scores to {SCORES_PATH}")


if __name__ == "__main__":
    main()
