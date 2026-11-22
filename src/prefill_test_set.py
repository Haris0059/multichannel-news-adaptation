import csv
import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import requests

from generate_posts import call_model
from llm_label import LABELS, RULES_END, RULES_PATH, parse_items, read_api_key

TASKS_DIR = Path("data/processed/test_tasks")
OUT_DIR = Path("data/processed/test_check")
# a cheap model that is not one of the NER training labellers (Opus, Sonnet, GPT)
MODEL = "google/gemini-3.8-flash"
EFFORT = "low"
WORKERS = 8
TEST_LABELS = ["correct", "changed", "added"]
COLUMNS = ["post_id", "post", "article", "fact", "type", "label", "source_fact"]

INSTRUCTIONS = (
    "You pre-label a test set. The user sends a source article and a post rewritten "
    "from it. List every fact in the POST, following the labelling rules above.\n"
    "For each fact say whether it is correct (the article states the same fact), "
    "changed (the article states this fact with a different value) or added "
    "(the article does not state it).\n"
    "Return only a JSON array. Each item is "
    '{"text": "...", "type": "...", "label": "...", "source": "..."}, where "text" is '
    "copied character for character from the post, type is one of "
    + ", ".join(LABELS)
    + ', label is one of correct, changed, added, and "source" is the matching text '
    "from the article, or an empty string for added facts."
)


def prefill(task, rules, api_key):
    data = task["data"]
    messages = [
        {"role": "system", "content": rules + "\n\n" + INSTRUCTIONS},
        {
            "role": "user",
            "content": f"ARTICLE:\n{data['article']}\n\nPOST:\n{data['post']}",
        },
    ]
    try:
        items = parse_items(call_model(MODEL, EFFORT, messages, api_key)) or []
    except requests.RequestException as e:
        print(f"{data['id']}: failed, left empty for the checker ({e})")
        items = []
    return [
        i
        for i in items
        if isinstance(i, dict)
        and i.get("type") in LABELS
        and i.get("label") in TEST_LABELS
        and i.get("text")
        and i["text"] in data["post"]
    ]


def main():
    api_key = read_api_key()
    rules = RULES_PATH.read_text(encoding="utf-8").split(RULES_END)[0]

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for path in sorted(TASKS_DIR.glob("*.json")):
        # never overwrite a sheet someone may already be checking
        if (OUT_DIR / f"{path.stem}.csv").exists():
            print(f"skipping {path.stem}, sheet already exists")
            continue
        with path.open("r", encoding="utf-8") as f:
            tasks = json.load(f)
        with ThreadPoolExecutor(WORKERS) as pool:
            facts = list(pool.map(lambda t: prefill(t, rules, api_key), tasks))

        # one row per fact; the post and article only on its first row.
        # utf-8-sig so Excel shows č, ć, š, ž, đ
        out_path = OUT_DIR / f"{path.stem}.csv"
        with out_path.open("w", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=COLUMNS)
            writer.writeheader()
            for task, items in zip(tasks, facts):
                data = task["data"]
                first = {"post": data["post"], "article": data["article"]}
                for item in items or [{}]:
                    writer.writerow(
                        {
                            "post_id": data["id"],
                            **first,
                            "fact": item.get("text", ""),
                            "type": item.get("type", ""),
                            "label": item.get("label", ""),
                            "source_fact": item.get("source", ""),
                        }
                    )
                    first = {}
        print(f"saved {sum(map(len, facts))} pre-filled facts to {out_path}")


if __name__ == "__main__":
    main()
