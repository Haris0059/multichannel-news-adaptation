import csv
import json
import sys
from pathlib import Path

# one post per line: id, channel, lang, model, prompt, injected, spans
GOLD_PATH = Path("data/processed/test_set.jsonl")
# one file per method, one post per line: id, spans
PREDICTIONS_DIR = Path("results/predictions")
OUT_DIR = Path("results/evaluation")
ERROR_LABELS = ("changed", "added")
SCORE_GROUPS = ("type", "channel", "lang")
RATE_GROUPS = ("channel", "lang", "type")


def read_jsonl(path):
    with path.open("r", encoding="utf-8") as f:
        return [json.loads(line) for line in f]


def write_csv(path, rows):
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def overlaps(a, b):
    return a["start"] < b["end"] and b["start"] < a["end"]


def outcome(post, span, result, gold_label, pred_label):
    return {
        "id": post["id"],
        "channel": post["channel"],
        "lang": post["lang"],
        "type": span["type"],
        "text": span["text"],
        "gold_label": gold_label,
        "pred_label": pred_label,
        "outcome": result,
    }


# A flagged fact counts when it overlaps a gold error of the same type, so a
# missed span costs recall and a false flag on a correct fact costs precision.
def align(post, predicted):
    unmatched = [s for s in post["spans"] if s["label"] in ERROR_LABELS]
    rows = []
    for pred in predicted:
        if pred["label"] not in ERROR_LABELS:
            continue
        gold = next(
            (g for g in unmatched if g["type"] == pred["type"] and overlaps(g, pred)),
            None,
        )
        if gold:
            unmatched.remove(gold)
            rows.append(outcome(post, gold, "tp", gold["label"], pred["label"]))
        else:
            rows.append(outcome(post, pred, "fp", None, pred["label"]))
    rows += [outcome(post, g, "fn", g["label"], None) for g in unmatched]
    return rows


def scores(rows):
    counts = {
        name: sum(r["outcome"] == name for r in rows) for name in ("tp", "fp", "fn")
    }
    tp, fp, fn = counts["tp"], counts["fp"], counts["fn"]
    return {
        **counts,
        "precision": tp / (tp + fp) if tp + fp else None,
        "recall": tp / (tp + fn) if tp + fn else None,
        "f1": 2 * tp / (2 * tp + fp + fn) if tp + fp + fn else None,
    }


def rows_for_label(rows, label):
    result = []
    for row in rows:
        gold_hit = row["gold_label"] == label
        pred_hit = row["pred_label"] == label
        if gold_hit or pred_hit:
            name = "tp" if gold_hit and pred_hit else "fn" if gold_hit else "fp"
            result.append({**row, "outcome": name})
    return result


def metric_rows(method, rows):
    result = [{"method": method, "group": "all", "value": "all", **scores(rows)}]
    for group in SCORE_GROUPS:
        for value in sorted({r[group] for r in rows}):
            subset = [r for r in rows if r[group] == value]
            result.append(
                {"method": method, "group": group, "value": value, **scores(subset)}
            )
    for label in ERROR_LABELS:
        subset = rows_for_label(rows, label)
        result.append(
            {"method": method, "group": "label", "value": label, **scores(subset)}
        )
    return result


def rate(facts):
    changed = sum(f["label"] == "changed" for f in facts)
    added = sum(f["label"] == "added" for f in facts)
    return {
        "facts": len(facts),
        "changed": changed,
        "added": added,
        "changed_rate": changed / len(facts),
        "added_rate": added / len(facts),
    }


# Injected errors are artificial, so those posts say nothing about how often an LLM
# changes facts. Model stays in the key so prompt effects are not mixed with model ones.
def rate_rows(posts):
    facts = [
        {
            "model": post["model"],
            "prompt": post["prompt"],
            "channel": post["channel"],
            "lang": post["lang"],
            **span,
        }
        for post in posts
        if not post["injected"]
        for span in post["spans"]
    ]

    result = []
    for key in sorted({(f["model"], f["prompt"]) for f in facts}):
        model, prompt = key
        subset = [f for f in facts if (f["model"], f["prompt"]) == key]
        base = {"model": model, "prompt": prompt}
        result.append({**base, "group": "all", "value": "all", **rate(subset)})
        for group in RATE_GROUPS:
            for value in sorted({f[group] for f in subset}):
                part = [f for f in subset if f[group] == value]
                result.append({**base, "group": group, "value": value, **rate(part)})
    return result


def show(value):
    return "-" if value is None else f"{value:.3f}"


def main():
    if not GOLD_PATH.exists():
        sys.exit(f"missing {GOLD_PATH}")
    paths = sorted(PREDICTIONS_DIR.glob("*.jsonl"))
    if not paths:
        sys.exit(f"no prediction files in {PREDICTIONS_DIR}")

    posts = read_jsonl(GOLD_PATH)
    metrics, errors = [], []
    for path in paths:
        predictions = {r["id"]: r["spans"] for r in read_jsonl(path)}
        missing = [p["id"] for p in posts if p["id"] not in predictions]
        if missing:
            sys.exit(
                f"{path} has no prediction for {len(missing)} posts: {missing[:5]}"
            )

        rows = [row for p in posts for row in align(p, predictions[p["id"]])]
        metrics += metric_rows(path.stem, rows)
        errors += [
            {"method": path.stem, **r} for r in rows if r["outcome"] in ("fp", "fn")
        ]

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    write_csv(OUT_DIR / "metrics.csv", metrics)
    if errors:
        write_csv(OUT_DIR / "errors.csv", errors)
    rates = rate_rows(posts)
    if rates:
        write_csv(OUT_DIR / "rates.csv", rates)

    for m in metrics:
        print(
            f"{m['method']:<12} {m['group']:<8} {m['value']:<12} "
            f"P {show(m['precision'])}  R {show(m['recall'])}  F1 {show(m['f1'])}  "
            f"tp {m['tp']} fp {m['fp']} fn {m['fn']}"
        )
    print(f"saved metrics, rates and {len(errors)} errors to {OUT_DIR}")


if __name__ == "__main__":
    main()
