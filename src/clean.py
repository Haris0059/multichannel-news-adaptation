import html
import json
import re
from pathlib import Path

RAW_DIR = Path("data/raw")
OUT_PATH = Path("data/processed/cleaned.jsonl")


def clean_html(raw):
    text = re.sub(r"</p>|<br\s*/?>|</li>|</h\d>", "\n", raw)
    text = re.sub(r"<.*?>", "", text)
    text = html.unescape(text)
    text = re.sub(r"[ \t\xa0]+", " ", text)
    text = "\n".join(line.strip() for line in text.splitlines() if line.strip())
    return text


def main():
    in_path = max(RAW_DIR.glob("articles_*.json"))
    with in_path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUT_PATH.open("w", encoding="utf-8") as f:
        for article in data:
            a = article["attributes"]

            record = {
                "title": a["Title"],
                "slug": a["Slug"],
                "date": a["Date"],
                "content": clean_html(a["Content"]),
            }
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    print(f"saved {len(data)} articles to {OUT_PATH}")


if __name__ == "__main__":
    main()
