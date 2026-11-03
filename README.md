# Multichannel News Adaptation

Detecting changed names, dates and numbers in LLM rewrites of IBU news. 
Developed as part of the Natural Language Processing course at International Burch University (Fall 2026).

## Setup
Requires Python 3.12.

```bash
git clone https://github.com/Haris0059/multichannel-news-adaptation.git
cd multichannel-news-adaptation
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pre-commit install
```

Activate the venv again in every new terminal.

Command to run to fetch,

## Annotator pilot

Before LLMs pre-label the NER training data, we pick the models by scoring them against our own labels on 50 train-split sentences. The rules are in `docs/labelling_rules.md`. All files under `data/processed/agreement/` are gitignored because they contain article text.

1. Sample 50 sentences, one per train article, half of them with a digit:

```bash
python src/sample_sentences.py   # sentences.jsonl and label_studio_tasks.json
```

2. Each of us labels them by hand in Label Studio (`pip install label-studio`, then `label-studio start`). Use `labelstudio/fact_spans.xml` as the labelling config and import `label_studio_tasks.json`. Export as JSON to `data/processed/agreement/human/<name>.json`. After we resolve our disagreements, export the agreed labels as `human/gold.json`.

3. Label the same sentences with the candidate models through Haris's API. Put the key in a `.env` file in the repo root, one line `HARIS_AI_KEY=sk-hr-...`. `.env` is gitignored; never commit the key.

```bash
python src/llm_label.py                               # all candidates in MODELS
python src/llm_label.py anthropic/claude-opus-5-5     # or one model
```

Raw replies are saved per model in `data/processed/agreement/llm/`. If the quota runs out, run the command again later, and it continues where it stopped.

4. Score everyone:

```bash
python src/agreement.py   # results/agreement_kappa.csv, results/annotator_scores.csv
```

The script computes token-level Cohen's kappa for every pair of annotators, and span precision, recall and F1 per fact type against `gold.json`. Spans match exactly after leading and trailing punctuation is trimmed.

