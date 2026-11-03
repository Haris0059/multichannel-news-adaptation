import json
from pathlib import Path

import matplotlib.pyplot as plt

IN_PATH = Path("data/processed/cleaned.jsonl")
SPLIT_PATH = Path("data/split.json")
FIG_DIR = Path("results/figures")


def plot_articles_per_year(articles):
    dates = [article["date"] for article in articles]
    years = [str[:4] for str in dates]

    year_counts = {year: years.count(year) for year in sorted(set(years))}

    plt.bar(year_counts.keys(), year_counts.values())
    plt.xlabel("Year")
    plt.ylabel("Number of Articles")
    plt.title("Number of Articles per Year")
    plt.xticks(rotation=45)
    plt.tight_layout()

    FIG_DIR.mkdir(parents=True, exist_ok=True)
    plt.savefig(FIG_DIR / "articles_per_year.png")
    plt.close()


def plot_words_per_article(articles):
    word_counts = [len(article["content"].split()) for article in articles]

    plt.hist(word_counts, bins=30, edgecolor="black")
    plt.xlabel("Number of Words")
    plt.ylabel("Number of Articles")
    plt.title("Distribution of Words per Article")
    plt.tight_layout()

    FIG_DIR.mkdir(parents=True, exist_ok=True)
    plt.savefig(FIG_DIR / "words_per_article.png")
    plt.close()


def main():
    with IN_PATH.open("r", encoding="utf-8") as f:
        articles = [json.loads(line) for line in f]

    plot_articles_per_year(articles)
    plot_words_per_article(articles)


if __name__ == "__main__":
    main()
