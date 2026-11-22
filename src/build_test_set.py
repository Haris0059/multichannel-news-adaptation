import csv
import json
import re
from pathlib import Path

from llm_label import LABELS

POSTS_PATH = Path("data/processed/posts.jsonl")
INJECTED_PATH = Path("data/processed/posts_injected.jsonl")
SHEETS_DIR = Path("data/processed/test_check")
OUT_PATH = Path("data/processed/test_set.jsonl")
TEST_LABELS = {"correct", "changed", "added"}


def read_jsonl(path):
    with path.open("r", encoding="utf-8") as f:
        return [json.loads(line) for line in f]


def find(fact, text, start):
    """Offsets of the next whole-word occurrence of fact, searching from start."""
    pattern = r"(?<!\w)" + re.escape(fact) + r"(?!\w)"
    m = re.compile(pattern).search(text, start) or re.compile(pattern).search(text)
    return (m.start(), m.end()) if m else None


def spans_from(rows, text, where):
    spans, pos = [], 0
    for row in rows:
        fact = row["fact"].strip()
        if not fact:
            continue
        fact_type = row["type"].strip().upper()
        label = row["label"].strip().lower()
        found = find(fact, text, pos)
        if fact_type not in LABELS or label not in TEST_LABELS or not found:
            print(f"{where}: skipped row {fact!r} {fact_type} {label}")
            continue
        start, end = found
        pos = end
        spans.append(
            {
                "start": start,
                "end": end,
                "text": fact,
                "type": fact_type,
                "label": label,
            }
        )
    return sorted(spans, key=lambda s: s["start"])


def main():
    posts = {p["id"]: p for p in read_jsonl(POSTS_PATH)}
    if INJECTED_PATH.exists():
        posts.update({p["id"]: p for p in read_jsonl(INJECTED_PATH)})

    out, missed = [], []
    for path in sorted(SHEETS_DIR.glob("*.csv")):
        with path.open("r", encoding="utf-8-sig", newline="") as f:
            rows = list(csv.DictReader(f))
        by_post = {}
        for row in rows:
            by_post.setdefault(row["post_id"].strip(), []).append(row)

        for post_id, post_rows in by_post.items():
            post = posts[post_id]
            spans = spans_from(post_rows, post["text"], f"{path.name} {post_id}")

            # the injected change should have been labelled "changed"
            change = post.get("change")
            if change and not any(
                s["label"] == "changed"
                and s["start"] < change["end"]
                and change["start"] < s["end"]
                for s in spans
            ):
                missed.append(post_id)

            out.append(
                {
                    "id": post_id,
                    "channel": post["channel"],
                    "lang": post["lang"],
                    "model": post["model"],
                    "prompt": post["prompt"],
                    "injected": post.get("injected", False),
                    "annotator": path.stem,
                    "spans": spans,
                }
            )

    with OUT_PATH.open("w", encoding="utf-8") as f:
        for row in sorted(out, key=lambda r: r["id"]):
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(f"saved {len(out)} posts to {OUT_PATH}")
    if missed:
        print(f"{len(missed)} injected changes are not labelled 'changed': {missed}")


if __name__ == "__main__":
    main()
