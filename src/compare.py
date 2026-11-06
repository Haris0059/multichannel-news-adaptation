from difflib import SequenceMatcher

from normalize import normalize

SOURCE_LANG = "en"
MIN_CHANGED_SIMILARITY = {"PERSON": 0.6, "ORG": 0.6, "DATE": 0, "NUMBER": 0}


def prepare(facts, lang):
    return [{**f, "value": normalize(f["text"], f["type"], lang)} for f in facts]


# A post may leave out a month or day but not add one. The year is looser because
# articles often omit it, so a post stating the year has not changed anything.
def date_part_matches(post, source):
    year_ok = post[0] is None or source[0] is None or post[0] == source[0]
    rest_ok = all(p is None or p == s for p, s in zip(post[1:], source[1:]))
    shared = any(p is not None and p == s for p, s in zip(post, source))
    return year_ok and rest_ok and shared


def matches(post, source, key):
    if post["type"] != source["type"]:
        return False

    a, b = post["value"], source["value"]
    if a is None or b is None:
        return post["text"].strip().lower() == source["text"].strip().lower()
    if post["type"] == "DATE":
        return date_part_matches(a["start"], b["start"]) and date_part_matches(
            a["end"], b["end"]
        )
    if post["type"] == "NUMBER":
        return a == b
    return set(a[key].split()) <= set(b[key].split())


def similarity(post, source, key):
    a, b = post["value"], source["value"]
    if a is None or b is None:
        return 0
    if post["type"] == "DATE":
        return sum(x == y for x, y in zip(a["start"], b["start"]) if x is not None) / 3
    if post["type"] == "NUMBER":
        return 1 - abs(a - b) / max(a, b, 1)

    source_words = b[key].split()
    scores = [
        max(SequenceMatcher(None, word, other).ratio() for other in source_words)
        for word in a[key].split()
    ]
    return sum(scores) / len(scores)


def identity(fact, key):
    if fact["value"] is None:
        return fact["text"].strip().lower()
    return fact["value"][key] if fact["type"] in ("PERSON", "ORG") else fact["value"]


def labelled(post, label, source=None):
    return {**post, "label": label, "source": source["text"] if source else None}


def compare_facts(source_facts, post_facts, post_lang):
    key = "exact" if post_lang == "en" else "stem"
    sources = prepare(source_facts, SOURCE_LANG)
    posts = prepare(post_facts, post_lang)
    results = [None] * len(posts)

    used = set()
    for i, post in enumerate(posts):
        found = [j for j, source in enumerate(sources) if matches(post, source, key)]
        if found:
            results[i] = labelled(post, "correct", sources[found[0]])
            used.update(found)

    pairs = []
    for i, post in enumerate(posts):
        for j, source in enumerate(sources):
            if results[i] or j in used or post["type"] != source["type"]:
                continue
            score = similarity(post, source, key)
            if score >= MIN_CHANGED_SIMILARITY[post["type"]]:
                pairs.append((-score, i, j))

    # A wrong value repeated in the post is one change, so it can share a source fact.
    taken = {}
    for _, i, j in sorted(pairs):
        post_id = identity(posts[i], key)
        if results[i] is None and taken.get(j, post_id) == post_id:
            results[i] = labelled(posts[i], "changed", sources[j])
            taken[j] = post_id

    return [r or labelled(post, "added") for r, post in zip(results, posts)]
