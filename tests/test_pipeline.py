import csv
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import evaluate
from compare import compare_facts
from normalize import normalize


def one(y, m, d):
    return {"start": (y, m, d), "end": (y, m, d)}


def span(a, b):
    return {"start": a, "end": b}


NORMALIZE_CASES = [
    # dates from the labelling rules
    ("October 21, 2026", "DATE", "en", one(2026, 10, 21)),
    ("21. oktobra 2026.", "DATE", "bs", one(2026, 10, 21)),
    ("21.10.", "DATE", "bs", one(None, 10, 21)),
    ("21. listopada", "DATE", "bs", one(None, 10, 21)),
    ("jul 2026.", "DATE", "bs", one(2026, 7, None)),
    ("2026/2027", "DATE", "en", span((2026, None, None), (2027, None, None))),
    ("21–23. oktobra 2026.", "DATE", "bs", span((2026, 10, 21), (2026, 10, 23))),
    # dates, edge cases
    ("21.10.2026.", "DATE", "bs", one(2026, 10, 21)),
    ("2026", "DATE", "en", one(2026, None, None)),
    ("October 2026", "DATE", "en", one(2026, 10, None)),
    ("October 21st", "DATE", "en", one(None, 10, 21)),
    ("21st of October 2026", "DATE", "en", one(2026, 10, 21)),
    ("2026-10-21", "DATE", "en", one(2026, 10, 21)),
    ("2026-10", "DATE", "en", one(2026, 10, None)),
    ("2026/27", "DATE", "en", span((2026, None, None), (2027, None, None))),
    ("2026-2027", "DATE", "en", span((2026, None, None), (2027, None, None))),
    ("October 21-23, 2026", "DATE", "en", span((2026, 10, 21), (2026, 10, 23))),
    ("October 5-7, 2026", "DATE", "en", span((2026, 10, 5), (2026, 10, 7))),
    ("21.10.-23.10.2026.", "DATE", "bs", span((2026, 10, 21), (2026, 10, 23))),
    ("21. do 23. oktobra 2026.", "DATE", "bs", span((2026, 10, 21), (2026, 10, 23))),
    ("OKTOBRA 2026", "DATE", "bs", one(2026, 10, None)),
    ("sijecnja 2026", "DATE", "bs", one(2026, 1, None)),
    ("siječnja 2026", "DATE", "bs", one(2026, 1, None)),
    ("proljeće 2026", "DATE", "bs", None),
    ("45.10.2026", "DATE", "bs", None),
    ("", "DATE", "en", None),
    # numbers from the labelling rules
    ("200", "NUMBER", "en", 200),
    ("five", "NUMBER", "en", 5),
    ("1.500", "NUMBER", "bs", 1500),
    ("1,500", "NUMBER", "en", 1500),
    ("1,5", "NUMBER", "bs", 1.5),
    ("1.5", "NUMBER", "en", 1.5),
    ("pet", "NUMBER", "bs", 5),
    ("dvadeset pet", "NUMBER", "bs", 25),
    ("dvadeset i pet", "NUMBER", "bs", 25),
    ("hiljadu", "NUMBER", "bs", 1000),
    ("tisuću", "NUMBER", "bs", 1000),
    ("1,5 miliona", "NUMBER", "bs", 1500000),
    ("20", "NUMBER", "bs", 20),
    # numbers, edge cases
    ("1,1 milion", "NUMBER", "bs", 1100000),
    ("1.1 million", "NUMBER", "en", 1100000),
    ("twenty-five", "NUMBER", "en", 25),
    ("one hundred and twenty", "NUMBER", "en", 120),
    ("a hundred", "NUMBER", "en", 100),
    ("two hundred thousand", "NUMBER", "en", 200000),
    ("hiljadu petsto", "NUMBER", "bs", 1500),
    ("pet stotina", "NUMBER", "bs", 500),
    ("dvije hiljade", "NUMBER", "bs", 2000),
    ("dvadeset pet hiljada", "NUMBER", "bs", 25000),
    ("milion petsto hiljada", "NUMBER", "bs", 1500000),
    ("2 hiljade", "NUMBER", "bs", 2000),
    ("1.500.000", "NUMBER", "bs", 1500000),
    ("1,500,000", "NUMBER", "en", 1500000),
    ("1.500,50", "NUMBER", "bs", 1500.5),
    ("1,500.50", "NUMBER", "en", 1500.5),
    ("1 500", "NUMBER", "bs", 1500),
    ("šest", "NUMBER", "bs", 6),
    ("sest", "NUMBER", "bs", 6),
    ("21.", "NUMBER", "bs", 21),
    ("20-30", "NUMBER", "en", None),
    ("mnogo", "NUMBER", "bs", None),
    ("5 studenata", "NUMBER", "bs", None),
]

SAME_STEM = [
    ("Amra Hodžić", "Amrom Hodžić"),
    ("Amra", "Amre"),
    ("Amra", "Amri"),
    ("Haris", "Harisom"),
    ("Fadil", "Fadila"),
    ("Hodžić", "Hodžićem"),
    ("Hodžić", "Hodžića"),
    ("Adem", "Adema"),
    ("Adem", "Ademom"),
    ("Adem", "Ademu"),
    ("Skeledžija", "Skeledžijom"),
    ("Mujo", "Mujom"),
    ("Mehmet Can", "Mehmetom Canom"),
]

DIFFERENT_STEM = [
    ("Skeledžija", "Skeledzija"),
    ("Hodžić", "Hodzic"),
    ("Hodžić", "Hadžić"),
    ("Amra", "Azra"),
    ("Mehmet", "Mehmed"),
]

SAME_ORG = [
    ("IBU", "International Burch University"),
    ("IBU", "IBU-a"),
    ("IBU", "IBU-om"),
    ("University of Sarajevo", "Univerzitetom u Sarajevu"),
    ("University of Sarajevo", "UNSA"),
    ("EU", "Evropskoj uniji"),
    ("EU", "EU-a"),
    ("International Burch University", "Internacionalnog univerziteta Burch"),
    ("IBU Faculty of Economics", "IBU faculty of economics"),
]


def stem(text):
    return normalize(text, "PERSON", "bs")["stem"]


@pytest.mark.parametrize("text, fact_type, lang, expected", NORMALIZE_CASES)
def test_normalize(text, fact_type, lang, expected):
    assert normalize(text, fact_type, lang) == expected


@pytest.mark.parametrize("a, b", SAME_STEM)
def test_inflected_names_share_a_stem(a, b):
    assert stem(a) == stem(b)


@pytest.mark.parametrize("a, b", DIFFERENT_STEM)
def test_changed_names_keep_different_stems(a, b):
    assert stem(a) != stem(b)


@pytest.mark.xfail(strict=True, reason="known limit: Petra loses the a of Petar")
def test_name_with_fleeting_a():
    assert stem("Petar") == stem("Petra")


@pytest.mark.xfail(strict=True, reason="known limit: Sanela strips to Sanel")
def test_male_and_female_name():
    assert stem("Sanel") != stem("Sanela")


@pytest.mark.parametrize("a, b", SAME_ORG)
def test_org_aliases(a, b):
    assert normalize(a, "ORG", "bs")["stem"] == normalize(b, "ORG", "bs")["stem"]


def facts(*items):
    return [{"text": text, "type": fact_type} for text, fact_type in items]


ARTICLE = facts(
    ("International Burch University", "ORG"),
    ("IBU", "ORG"),
    ("University of Sarajevo", "ORG"),
    ("Mehmet Can", "PERSON"),
    ("Amra Hodžić", "PERSON"),
    ("October 21, 2026", "DATE"),
    ("200", "NUMBER"),
    ("five", "NUMBER"),
    ("1,500", "NUMBER"),
)

COMPARE_CASES = [
    (
        "bosnian post, all correct",
        ARTICLE,
        facts(
            ("Internacionalni univerzitet Burch", "ORG"),
            ("IBU-a", "ORG"),
            ("Univerzitetom u Sarajevu", "ORG"),
            ("Amrom Hodžić", "PERSON"),
            ("Hodžić", "PERSON"),
            ("21. oktobra 2026.", "DATE"),
            ("21.10.", "DATE"),
            ("oktobra 2026.", "DATE"),
            ("2026", "DATE"),
            ("200", "NUMBER"),
            ("pet", "NUMBER"),
            ("1.500", "NUMBER"),
        ),
        "bs",
        ["correct"] * 12,
    ),
    (
        "english post, all correct",
        ARTICLE,
        facts(
            ("IBU", "ORG"),
            ("Amra Hodžić", "PERSON"),
            ("Can", "PERSON"),
            ("October 21", "DATE"),
            ("5", "NUMBER"),
        ),
        "en",
        ["correct"] * 5,
    ),
    (
        "changed date, name and number",
        ARTICLE,
        facts(
            ("22. oktobra 2026.", "DATE"),
            ("Amrom Hadžić", "PERSON"),
            ("250", "NUMBER"),
        ),
        "bs",
        ["changed"] * 3,
    ),
    (
        "missing diacritic is changed",
        facts(("Haris Skeledžija", "PERSON")),
        facts(("Haris Skeledzija", "PERSON")),
        "bs",
        ["changed"],
    ),
    (
        "invented person is added even with an unused source person",
        facts(("Mehmet Can", "PERSON")),
        facts(("Jelena Petrović", "PERSON")),
        "bs",
        ["added"],
    ),
    (
        "more post numbers than unused source numbers",
        facts(("200", "NUMBER")),
        facts(("210", "NUMBER"), ("9", "NUMBER")),
        "en",
        ["changed", "added"],
    ),
    (
        "closest number takes the source pair",
        facts(("200", "NUMBER")),
        facts(("9", "NUMBER"), ("210", "NUMBER")),
        "en",
        ["added", "changed"],
    ),
    (
        "invented day is not correct",
        facts(("October 2026", "DATE")),
        facts(("October 21, 2026", "DATE")),
        "en",
        ["changed"],
    ),
    (
        "post adding the year is correct",
        facts(("October 21", "DATE")),
        facts(("October 21, 2026", "DATE")),
        "en",
        ["correct"],
    ),
    (
        "wrong year is changed",
        facts(("October 21, 2026", "DATE")),
        facts(("October 21, 2025", "DATE")),
        "en",
        ["changed"],
    ),
    (
        "repeated wrong value is changed each time",
        facts(("Amra Hodžić", "PERSON")),
        facts(("Amra Hadžić", "PERSON"), ("Amrom Hadžić", "PERSON")),
        "bs",
        ["changed", "changed"],
    ),
    (
        "two different wrong values use one source fact once",
        facts(("200", "NUMBER")),
        facts(("210", "NUMBER"), ("220", "NUMBER")),
        "en",
        ["changed", "added"],
    ),
    (
        "english post inflection is a change",
        facts(("Haris", "PERSON")),
        facts(("Harisa", "PERSON")),
        "en",
        ["changed"],
    ),
    (
        "source fact left out of post is not an error",
        ARTICLE,
        facts(("IBU", "ORG")),
        "en",
        ["correct"],
    ),
    (
        "unparsed values match on text",
        facts(("20-30", "NUMBER")),
        facts(("20-30", "NUMBER")),
        "bs",
        ["correct"],
    ),
    (
        "unparsed value against a different number is changed",
        facts(("200", "NUMBER")),
        facts(("desetak", "NUMBER")),
        "bs",
        ["changed"],
    ),
    (
        "type must agree",
        facts(("2026", "DATE")),
        facts(("2026", "NUMBER")),
        "en",
        ["added"],
    ),
    ("empty post", ARTICLE, [], "bs", []),
    ("empty source", [], facts(("IBU", "ORG")), "bs", ["added"]),
]


@pytest.mark.parametrize(
    "source, post, lang, expected",
    [case[1:] for case in COMPARE_CASES],
    ids=[case[0] for case in COMPARE_CASES],
)
def test_compare_facts(source, post, lang, expected):
    assert [r["label"] for r in compare_facts(source, post, lang)] == expected


def gold(start, end, fact_type, label):
    return {
        "text": f"s{start}",
        "type": fact_type,
        "start": start,
        "end": end,
        "label": label,
    }


POSTS = [
    {
        "id": "p1",
        "channel": "instagram",
        "lang": "en",
        "model": "gemini",
        "prompt": "fact_rule",
        "injected": False,
        "spans": [
            gold(0, 5, "PERSON", "changed"),
            gold(10, 15, "DATE", "correct"),
            gold(20, 25, "NUMBER", "added"),
        ],
    },
    {
        "id": "p2",
        "channel": "linkedin",
        "lang": "bs",
        "model": "weak",
        "prompt": "no_rule",
        "injected": True,
        "spans": [gold(0, 5, "DATE", "changed")],
    },
]
PREDICTIONS = [
    {
        "id": "p1",
        "spans": [gold(0, 4, "PERSON", "changed"), gold(10, 15, "DATE", "changed")],
    },
    {
        "id": "p2",
        "spans": [gold(0, 5, "DATE", "added"), gold(30, 35, "ORG", "added")],
    },
]


def write_jsonl(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")


def read_csv(path):
    with path.open("r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


@pytest.fixture
def outputs(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    write_jsonl(tmp_path / "data/processed/test_set.jsonl", POSTS)
    write_jsonl(tmp_path / "results/predictions/baseline.jsonl", PREDICTIONS)
    perfect = [{"id": p["id"], "spans": p["spans"]} for p in POSTS]
    write_jsonl(tmp_path / "results/predictions/perfect.jsonl", perfect)
    evaluate.main()
    out = tmp_path / "results/evaluation"
    return {
        "metrics": read_csv(out / "metrics.csv"),
        "rates": read_csv(out / "rates.csv"),
        "errors": read_csv(out / "errors.csv"),
    }


def metric(outputs, method, group, value):
    return next(
        m
        for m in outputs["metrics"]
        if (m["method"], m["group"], m["value"]) == (method, group, value)
    )


def counts(m):
    return m["tp"], m["fp"], m["fn"]


def test_overall_scores(outputs):
    m = metric(outputs, "baseline", "all", "all")
    assert counts(m) == ("2", "2", "1")
    assert float(m["precision"]) == pytest.approx(0.5)
    assert float(m["recall"]) == pytest.approx(2 / 3)
    assert float(m["f1"]) == pytest.approx(4 / 7)


def test_label_scores_need_the_exact_label(outputs):
    assert counts(metric(outputs, "baseline", "label", "changed")) == ("1", "1", "1")
    assert counts(metric(outputs, "baseline", "label", "added")) == ("0", "2", "1")


def test_group_scores(outputs):
    assert counts(metric(outputs, "baseline", "lang", "bs")) == ("1", "1", "0")
    assert counts(metric(outputs, "baseline", "type", "NUMBER")) == ("0", "0", "1")


def test_perfect_method(outputs):
    m = metric(outputs, "perfect", "all", "all")
    assert float(m["f1"]) == pytest.approx(1.0)
    assert (m["fp"], m["fn"]) == ("0", "0")


def test_error_list(outputs):
    assert {e["method"] for e in outputs["errors"]} == {"baseline"}
    assert len(outputs["errors"]) == 3


def test_rates_leave_out_injected_posts(outputs):
    assert {r["model"] for r in outputs["rates"]} == {"gemini"}
    r = next(r for r in outputs["rates"] if r["group"] == "all")
    assert r["facts"] == "3"
    assert float(r["changed_rate"]) == pytest.approx(1 / 3)
    assert float(r["added_rate"]) == pytest.approx(1 / 3)


@pytest.mark.parametrize(
    "gold_spans, predicted, expected",
    [
        (
            [gold(0, 5, "DATE", "changed")],
            [gold(0, 5, "NUMBER", "changed")],
            ["fn", "fp"],
        ),
        (
            [gold(0, 5, "DATE", "changed")],
            [gold(5, 9, "DATE", "changed")],
            ["fn", "fp"],
        ),
        (
            [gold(0, 10, "DATE", "changed")],
            [gold(0, 4, "DATE", "changed"), gold(5, 9, "DATE", "changed")],
            ["fp", "tp"],
        ),
    ],
    ids=["wrong type", "touching spans", "one gold fact matches once"],
)
def test_align(gold_spans, predicted, expected):
    rows = evaluate.align({**POSTS[1], "spans": gold_spans}, predicted)
    assert sorted(r["outcome"] for r in rows) == expected


def test_scores_with_no_flags():
    assert evaluate.scores([])["f1"] is None


def test_missing_prediction_stops_the_run(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    write_jsonl(tmp_path / "data/processed/test_set.jsonl", POSTS)
    write_jsonl(tmp_path / "results/predictions/partial.jsonl", PREDICTIONS[:1])
    with pytest.raises(SystemExit, match="no prediction"):
        evaluate.main()
