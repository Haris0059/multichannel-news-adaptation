import json
import os
import re
import sys
import time
from datetime import date
from pathlib import Path

import requests

API_URL = "https://ai.haris.rip/api/v1/chat/completions"
API_KEY_ENV = "HARIS_AI_KEY"
ENV_PATH = Path(".env")
# pilot candidates; on 03.11.2026 only gemini-3.8-flash answered among the Gemini models.
# it also writes the posts, so check its scores on Bosnian posts before using it there
MODELS = [
    "anthropic/claude-opus-5-5",
    "anthropic/claude-sonnet-5-5",
    "google/gemini-3.8-flash-high",
    "openai/gpt-oss-120b-medium",
    "mistral/ministral-14b-latest",
]
LABELS = ["PERSON", "ORG", "DATE", "NUMBER"]
SENTENCES_PATH = Path("data/processed/agreement/sentences.jsonl")
RULES_PATH = Path("docs/labelling_rules.md")
OUT_DIR = Path("data/processed/agreement/llm")
TIMEOUT = 360
RETRIES = 3
# the API is rate limited: wait between requests, and longer after an error
MIN_INTERVAL = 5
RETRY_WAIT = 30
# only the rule sections go into the prompt, not the open questions and normalisation notes
RULES_END = "\n## Open questions"

INSTRUCTIONS = (
    "You are an annotator. Label the facts in the sentence the user sends, "
    "following the labelling rules above exactly.\n"
    "Return only a JSON array and no other text. Each item is "
    '{"text": "...", "type": "..."}, where "text" is copied character for '
    'character from the sentence and "type" is one of ' + ", ".join(LABELS) + ".\n"
    "List every mention in the order it appears. Return [] if there are no facts."
)


def read_api_key():
    """Take the key from the environment, or from the gitignored .env file."""
    if os.environ.get(API_KEY_ENV):
        return os.environ[API_KEY_ENV]
    if ENV_PATH.exists():
        for line in ENV_PATH.read_text(encoding="utf-8").splitlines():
            name, _, value = line.partition("=")
            if name.strip() == API_KEY_ENV:
                return value.strip()
    return None


def model_path(model):
    return OUT_DIR / f"{model.replace('/', '__')}.jsonl"


last_call = 0.0


def wait_turn():
    global last_call
    time.sleep(max(0.0, MIN_INTERVAL - (time.monotonic() - last_call)))
    last_call = time.monotonic()


def call_model(model, messages, api_key):
    headers = {"Authorization": f"Bearer {api_key}"}
    body = {"model": model, "messages": messages}
    for attempt in range(1, RETRIES + 1):
        wait_turn()
        response = requests.post(API_URL, headers=headers, json=body, timeout=TIMEOUT)
        if response.status_code == 429:
            sys.exit(f"{model}: quota used up, run again later\n{response.text}")
        if response.status_code in (502, 503) and attempt < RETRIES:
            time.sleep(RETRY_WAIT * attempt)
            continue
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]


def parse_items(raw):
    # models without a JSON mode sometimes wrap the array in ```json fences or prose
    match = re.search(r"\[.*\]", raw, re.DOTALL)
    if not match:
        return None
    try:
        items = json.loads(match.group())
    except json.JSONDecodeError:
        return None
    return items if isinstance(items, list) else None


def locate(items, sentence):
    """Turn {"text", "type"} items into spans with offsets; reject what is not in the sentence."""
    spans, rejected, used = [], [], set()
    for item in items:
        if not isinstance(item, dict) or item.get("type") not in LABELS:
            rejected.append(item)
            continue
        text = item.get("text") or ""
        # a repeated mention goes to the next unused occurrence
        start = sentence.find(text) if text else -1
        while start in used:
            start = sentence.find(text, start + 1)
        if start == -1:
            rejected.append(item)
            continue
        used.add(start)
        end = start + len(text)
        spans.append({"text": text, "type": item["type"], "start": start, "end": end})
    return spans, rejected


def label_with(model, sentences, rules, api_key):
    out_path = model_path(model)
    done = set()
    if out_path.exists():
        with out_path.open("r", encoding="utf-8") as f:
            done = {json.loads(line)["id"] for line in f}

    todo = [s for s in sentences if s["id"] not in done]
    with out_path.open("a", encoding="utf-8") as f:
        for n, sentence in enumerate(todo, 1):
            messages = [
                {"role": "system", "content": rules + "\n\n" + INSTRUCTIONS},
                {"role": "user", "content": sentence["text"]},
            ]
            raw = call_model(model, messages, api_key)
            items = parse_items(raw)
            spans, rejected = locate(items or [], sentence["text"])
            record = {
                "id": sentence["id"],
                "model": model,
                "date": date.today().isoformat(),
                "raw": raw,
                "parsed": items is not None,
                "spans": spans,
                "rejected": rejected,
            }
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
            f.flush()
            print(f"{model}: {len(done) + n}/{len(sentences)}")

    print(f"saved {len(sentences)} labelled sentences to {out_path}")


def main():
    api_key = read_api_key()
    if not api_key:
        sys.exit(f"put {API_KEY_ENV}=sk-hr-... in {ENV_PATH} first")

    rules = RULES_PATH.read_text(encoding="utf-8").split(RULES_END)[0]
    with SENTENCES_PATH.open("r", encoding="utf-8") as f:
        sentences = [json.loads(line) for line in f]

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for model in sys.argv[1:] or MODELS:
        try:
            label_with(model, sentences, rules, api_key)
        except requests.RequestException as e:
            # skip a broken model; its finished sentences stay saved for the next run
            print(f"{model}: failed, skipping ({e})")


if __name__ == "__main__":
    main()
