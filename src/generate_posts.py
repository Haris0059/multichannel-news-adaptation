import json
import random
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date
from pathlib import Path

import requests

from llm_label import API_URL, RETRIES, RETRY_WAIT, TIMEOUT, read_api_key

ARTICLES_PATH = Path("data/processed/cleaned.jsonl")
SPLIT_PATH = Path("data/split.json")
OUT_PATH = Path("data/processed/posts.jsonl")
SEED = 42
# requests run in parallel; Mistral's free plan rate-limits, so it gets fewer at once
WORKERS = 8
MISTRAL_WORKERS = 2
mistral_slots = threading.Semaphore(MISTRAL_WORKERS)

# (tag, model, effort, prompt); the proposal's setup is gemini with the fact rule.
# the test split also gets gemini without the rule (prompt effect) and a weak model
# without the rule (more errors to find)
MAIN_VARIANT = ("gemini", "google/gemini-3.8-flash", "low", "fact_rule")
TEST_VARIANTS = [
    MAIN_VARIANT,
    ("gemini", "google/gemini-3.8-flash", "low", "no_rule"),
    ("weak", "mistral/ministral-8b-latest", None, "no_rule"),
]
CHANNELS = {
    "instagram": "an Instagram caption: 2 to 4 short sentences, a friendly tone, "
    "a few emojis and 3 to 5 hashtags at the end",
    "linkedin": "a LinkedIn post: 80 to 150 words, a professional tone, "
    "1 to 3 hashtags at the end",
    "website": "a website news summary: 40 to 70 words, a neutral tone, "
    "no emojis or hashtags",
}
LANGUAGES = {"en": "English", "bs": "Bosnian (Latin script)"}
FACT_RULE = (
    "Keep every name, organisation, place, date, time and number exactly as in the "
    "article. Do not add facts that are not in the article."
)


def post_id(slug, channel, lang, tag, prompt):
    return f"{slug}__{channel}__{lang}__{tag}__{prompt}"


def messages_for(article, channel, lang, prompt):
    instruction = (
        f"Rewrite the IBU news article below as {CHANNELS[channel]}. "
        f"Write in {LANGUAGES[lang]}. Return only the post text."
    )
    if prompt == "fact_rule":
        instruction += " " + FACT_RULE
    return [
        {
            "role": "system",
            "content": "You write posts for International Burch University (IBU).",
        },
        {
            "role": "user",
            "content": f"{instruction}\n\nTitle: {article['title']}\n\n{article['content']}",
        },
    ]


def call_model(model, effort, messages, api_key):
    headers = {"Authorization": f"Bearer {api_key}"}
    body = {"model": model, "messages": messages}
    if effort:
        body["reasoning_effort"] = effort
    for attempt in range(1, RETRIES + 1):
        response = requests.post(API_URL, headers=headers, json=body, timeout=TIMEOUT)
        # 502/503 are safe to retry; a Mistral 429 is its free-plan rate limit
        retry = response.status_code in (502, 503) or (
            response.status_code == 429 and model.startswith("mistral/")
        )
        if retry and attempt < RETRIES:
            time.sleep(RETRY_WAIT * attempt)
            continue
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"].strip()


def generate(job, api_key):
    article, split, (tag, model, effort, prompt), channel, lang = job
    messages = messages_for(article, channel, lang, prompt)
    if model.startswith("mistral/"):
        with mistral_slots:
            text = call_model(model, effort, messages, api_key)
    else:
        text = call_model(model, effort, messages, api_key)
    return {
        "id": post_id(article["slug"], channel, lang, tag, prompt),
        "slug": article["slug"],
        "split": split,
        "channel": channel,
        "lang": lang,
        "model": tag,
        "model_id": model,
        "prompt": prompt,
        "date": date.today().isoformat(),
        "text": text,
    }


def main():
    api_key = read_api_key()
    if not api_key:
        sys.exit("put HARIS_AI_KEY=sk-hr-... in .env first")
    # e.g. "test", "train val", and an optional number to stop after that many posts
    splits = [a for a in sys.argv[1:] if not a.isdigit()] or ["test"]
    limit = next((int(a) for a in sys.argv[1:] if a.isdigit()), None)

    with SPLIT_PATH.open("r", encoding="utf-8") as f:
        split_of = {
            slug: name for name, slugs in json.load(f).items() for slug in slugs
        }
    with ARTICLES_PATH.open("r", encoding="utf-8") as f:
        articles = [json.loads(line) for line in f]

    jobs = []
    for article in sorted(articles, key=lambda a: a["slug"]):
        split = split_of[article["slug"]]
        if split not in splits:
            continue
        variants = TEST_VARIANTS if split == "test" else [MAIN_VARIANT]
        for variant in variants:
            for channel in CHANNELS:
                for lang in LANGUAGES:
                    jobs.append((article, split, variant, channel, lang))
    # shuffled, so a run stopped early still covers every channel, language and model
    random.Random(SEED).shuffle(jobs)

    done = set()
    if OUT_PATH.exists():
        with OUT_PATH.open("r", encoding="utf-8") as f:
            done = {json.loads(line)["id"] for line in f}
    todo = [
        job
        for job in jobs
        if post_id(job[0]["slug"], job[3], job[4], job[2][0], job[2][3]) not in done
    ][:limit]

    # only this thread writes the file, so lines never mix
    failed = 0
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUT_PATH.open("a", encoding="utf-8") as f, ThreadPoolExecutor(WORKERS) as pool:
        futures = {pool.submit(generate, job, api_key): job for job in todo}
        for n, future in enumerate(as_completed(futures), 1):
            try:
                record = future.result()
            except requests.RequestException as e:
                # skipped; the next run tries it again
                failed += 1
                print(f"{n}/{len(todo)} failed: {e}")
                continue
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
            f.flush()
            print(f"{n}/{len(todo)} {record['id']}")

    print(f"saved {len(todo) - failed} posts to {OUT_PATH}, {failed} failed")


if __name__ == "__main__":
    main()
