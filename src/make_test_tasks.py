import json
import random
from itertools import cycle
from pathlib import Path

ARTICLES_PATH = Path("data/processed/cleaned.jsonl")
POSTS_PATH = Path("data/processed/posts.jsonl")
INJECTED_PATH = Path("data/processed/posts_injected.jsonl")
OUT_DIR = Path("data/processed/test_tasks")
SEED = 42
ANNOTATORS = ["fadil", "haris", "abdurrahman"]
# 4 groups x 15 = 60 posts, 20 per annotator
PER_GROUP = 15


def read_jsonl(path):
    with path.open("r", encoding="utf-8") as f:
        return [json.loads(line) for line in f]


def group_of(post):
    if post.get("injected"):
        return "injected"
    return f"{post['model']}/{post['prompt']}"


def pick(posts, n, rng):
    """Take n posts, spread over channel and language."""
    cells = {}
    for post in sorted(posts, key=lambda p: p["id"]):
        cells.setdefault((post["channel"], post["lang"]), []).append(post)
    for cell in cells.values():
        rng.shuffle(cell)

    picked = []
    for key in cycle(sorted(cells)):
        if len(picked) == n or not any(cells.values()):
            break
        if cells[key]:
            picked.append(cells[key].pop())
    return picked


def main():
    articles = {a["slug"]: a for a in read_jsonl(ARTICLES_PATH)}
    injected = read_jsonl(INJECTED_PATH) if INJECTED_PATH.exists() else []
    # an injected post replaces its clean original, so no text is labelled twice
    replaced = {p["source_id"] for p in injected}
    pool = [
        p
        for p in read_jsonl(POSTS_PATH)
        if p["split"] == "test" and p["id"] not in replaced
    ] + injected

    groups = {}
    for post in pool:
        groups.setdefault(group_of(post), []).append(post)

    rng = random.Random(SEED)
    chosen = []
    for name in sorted(groups):
        part = pick(groups[name], PER_GROUP, rng)
        print(f"{name}: {len(part)} posts")
        chosen += part

    # labellers do not see the model, prompt or whether an error was injected
    tasks = {name: [] for name in ANNOTATORS}
    for annotator, post in zip(cycle(ANNOTATORS), chosen):
        article = articles[post["slug"]]
        tasks[annotator].append(
            {
                "data": {
                    "id": post["id"],
                    "channel": post["channel"],
                    "lang": post["lang"],
                    "post": post["text"],
                    "article": f"{article['title']}\n\n{article['content']}",
                }
            }
        )

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for annotator, items in tasks.items():
        out_path = OUT_DIR / f"{annotator}.json"
        with out_path.open("w", encoding="utf-8") as f:
            json.dump(items, f, ensure_ascii=False, indent=2)
        print(f"saved {len(items)} posts to {out_path}")


if __name__ == "__main__":
    main()
