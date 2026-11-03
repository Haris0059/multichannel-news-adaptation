import json
from datetime import date
from pathlib import Path

import requests

URL = "https://cms.ibu.edu.ba/graphql"
QUERY = """
{
  articles(pagination: {pageSize: 200}, sort: "Date:desc") {
    meta { pagination { total } }
    data { attributes { Title Slug Date Content } }
  }
}
"""
OUT_DIR = Path("data/raw")


def main():
    response = requests.post(URL, json={"query": QUERY}, timeout=60)
    response.raise_for_status()
    data = response.json()

    articles = data["data"]["articles"]["data"]
    total = data["data"]["articles"]["meta"]["pagination"]["total"]
    assert len(articles) == total, f"got {len(articles)} of {total}"

    today = date.today().isoformat()
    out_path = OUT_DIR / f"articles_{today}.json"

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(articles, f, ensure_ascii=False, indent=2)

    print(f"saved {len(articles)} articles to {out_path}")


if __name__ == "__main__":
    main()
