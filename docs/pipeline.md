# Pipeline

Draft · 22.11.2026 · Abdurrahman

How an IBU article becomes a score. Solid boxes are written; dashed boxes are still to do.

```mermaid
flowchart TD
    cms[(IBU CMS<br/>GraphQL API)]
    fetch[fetch_articles.py<br/>raw articles]
    clean[clean.py<br/>cleaned.jsonl]
    split[split.py<br/>train / val / test by article]
    analyze[analyze.py<br/>charts]

    rules[labelling_rules.md<br/>6 fact types]
    llmlabel[llm_label.py<br/>LLM labels on train]
    finetune[NER fine-tuning]

    generate[post generation<br/>channels × EN/BS × models × prompts<br/>+ injected errors]
    testset[hand-labelled test set<br/>test articles and their posts]
    baseline[baseline<br/>regex / spaCy / CLASSLA]
    predict[predictions<br/>one file per method]

    normalize[normalize.py<br/>comparable values]
    compare[compare.py<br/>correct / changed / added]
    evaluate[evaluate.py<br/>P / R / F1, change rates, error list]
    errors[error analysis]

    cms --> fetch --> clean --> split
    clean --> analyze
    split -- train --> llmlabel
    rules --> llmlabel --> finetune
    rules --> testset
    split -- test --> generate --> testset
    generate --> baseline
    generate --> finetune
    baseline --> predict
    finetune --> predict
    predict --> normalize --> compare --> evaluate
    testset --> evaluate
    evaluate --> errors

    classDef todo stroke-dasharray: 5 5
    class generate,testset,baseline,predict,finetune,errors todo
```

## Stages and owners

| Stage | Files | Owner | Status |
| --- | --- | --- | --- |
| Data: fetch, clean, split, analysis | `src/fetch_articles.py`, `src/clean.py`, `src/split.py`, `src/analyze.py` | Haris | Done |
| Annotation schema | `docs/labelling_rules.md` | Fadil | v0.2 draft, 3 open questions |
| LLM labels for NER training | `src/llm_label.py` | Fadil | Run on the train split by Haris (22.11); the Gemini file is empty |
| NER fine-tuning | | Fadil | To do |
| Post generation and injected errors | `src/generate_posts.py`, `src/inject_errors.py` | Haris, written by Fadil | Written 22.11, tested with a fake API, not run yet |
| Test set | `src/make_test_tasks.py`, `src/prefill_test_set.py`, `src/build_test_set.py` → `data/processed/test_set.jsonl` | Haris, labelled by all | 60 posts pre-labelled by Gemini 22.11; team check to do |
| Baseline | `src/baseline.py` | Haris, written by Fadil | Written 22.11, not run on real posts |
| Normalisation, comparison, evaluation | `src/normalize.py`, `src/compare.py`, `src/evaluate.py` | Abdurrahman | Done, 170 tests |
| Annotation, cross-review, error analysis | | All | To do |

## What flows between stages

- A **fact** is a span `{text, type, start, end}` with one of PERSON, ORG, LOC, DATE, TIME, NUMBER.
- Each method finds facts in the source article and in the post. `compare.py` labels every post fact as `correct`, `changed` or `added`.
- `evaluate.py` scores those labels against the test set, where `changed` and `added` are the errors to catch. It also reports how often each model and prompt changes facts, leaving out the posts with injected errors.
- Most source articles are English. Four are Bosnian, so `compare_facts` takes the source language as an argument.
