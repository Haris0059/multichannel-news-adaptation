import json
import random
from pathlib import Path

IN_PATH = Path("data/processed/cleaned.jsonl")
OUT_PATH = Path("data/split.json")
SEED = 42


def split_slugs(slugs):
    slugs = sorted(slugs)
    random.Random(SEED).shuffle(slugs)

    n = len(slugs)
    a = int(n * 0.7)
    b = int(n * 0.85)

    return slugs[:a], slugs[a:b], slugs[b:]


def main():
    with IN_PATH.open("r") as f:
        slugs = [json.loads(line)["slug"] for line in f]

        train, val, test = split_slugs(slugs)

        assert len(train) + len(val) + len(test) == len(slugs)

        with OUT_PATH.open("w", encoding="utf-8") as f:
            json.dump({"train": train, "val": val, "test": test}, f, indent=2)
    print(
        f"saved {len(train)} train, {len(val)} val, {len(test)} test slugs to {OUT_PATH}"
    )


if __name__ == "__main__":
    main()
