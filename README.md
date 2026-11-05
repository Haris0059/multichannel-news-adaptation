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

## LLM labelling

Put Haris's API key in a gitignored `.env` file in the repo root (`HARIS_AI_KEY=sk-hr-...`), then run `python src/llm_label.py` to label the train-split articles with every model in `MODELS`, or `python src/llm_label.py <model>` for one model.
Labels are saved per model in `data/processed/llm_labels/`; if the quota runs out, run it again later and it continues where it stopped.
