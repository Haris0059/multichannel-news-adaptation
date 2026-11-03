import html
import json
import re
from pathlib import Path


def clean_html(raw):
    text = re.sub(r"</p>|<br\s*/?>|</li>|</h\d>", "\n", raw)
    text = re.sub(r"<.*?>", "", text)
    text = html.unescape(text)
    text = re.sub(r"[ \t\xa0]+", " ", text)
    text = "\n".join(line.strip() for line in text.splitlines() if line.strip())
    return text


def main():
    input_path = Path("data/raw/articles_2026-11-02.json")
    output_path = Path("data/processed/cleaned.jsonl")

    with input_path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as out:
        for article in data:
            a = article["attributes"]

            record = {
                "title": a["Title"],
                "slug": a["Slug"],
                "date": a["Date"],
                "content": clean_html(a["Content"]),
            }
            out.write(json.dumps(record, ensure_ascii=False) + "\n")

        print(f"wrote {len(data)} articles to {output_path}")


if __name__ == "__main__":
    main()
