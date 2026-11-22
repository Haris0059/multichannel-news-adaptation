# Contributions

## Haris Skeledžija
- 24.10.2026 - Drafted the project proposal
- 24.10.2026 - Identified the IBU CMS (GraphQL API) as data source
- 02.11.2026 - Set up the Python project: virtual environment, requirements, Ruff linter, pre-commit hook
- 02.11.2026 - Wrote setup instructions in README
- 02.11.2026 - Wrote the article fetch script (`src/fetch_articles.py`)
- 03.11.2026 - Wrote the HTML cleaning script (`src/clean.py`)
- 03.11.2026 - Unified the style of both scripts; clean script reads the newest raw file (applied with AI assistance)
- 03.11.2026 - Wrote the article-level train/val/test split (`src/split.py`, `data/split.json`)
- 03.11.2026 - Wrote the data analysis script and charts (`src/analyze.py`, `results/figures/`)
- 03.11.2026 - Added shared Claude Code skills for the team (commit message, PR description, ADHD mode)
- 05.11.2026 - Reviewed Fadil's LLM labelling PR (#2): set the annotator models and asked to cut the pilot (reviewed with AI assistance)

## Fadil Masnopita
- 24.10.2026 - Divided the responsibilities as equally as possible
- 03.11.2026 - Drafted the labelling rules for fact spans (`docs/labelling_rules.md`, applied with AI assistance)
- 03.11.2026 - Wrote the LLM labelling script for the train-split articles (`src/llm_label.py`, applied with AI assistance)
- 03.11.2026 - Fixed the file encoding in `src/split.py` so it runs on Windows
- 07.11.2026 - Fixed `locate()` in `src/llm_label.py` so a short number inside a longer one is not matched
- 22.11.2026 - Wrote post generation and error injection (`src/generate_posts.py`, `src/inject_errors.py`, applied with AI assistance)
- 22.11.2026 - Set up test set v1: post selection, Gemini pre-labelling and check sheets, conversion to the evaluation format (`src/make_test_tasks.py`, `src/prefill_test_set.py`, `src/build_test_set.py`, applied with AI assistance)
- 22.11.2026 - Wrote the rule-based baseline (`src/baseline.py`, applied with AI assistance)
- 22.11.2026 - Wrote the README pipeline diagram and data section (applied with AI assistance)
- 22.11.2026 - Built test set v1 (60 posts) with AI pre-labelling and AI correction; team manual check still to do (applied with AI assistance)
- 22.11.2026 - Ran the baseline and the first evaluation on test set v1 (`results/`)

## Abdurrahman Beširović
- 06.11.2026 - Wrote the fact normalisation for dates, numbers, names and organisations (`src/normalize.py`, applied with AI assistance)
- 06.11.2026 - Wrote the fact comparison that labels post facts as correct, changed or added (`src/compare.py`, applied with AI assistance)
- 06.11.2026 - Wrote the evaluation script for scores, fact change rates and the error list (`src/evaluate.py`, applied with AI assistance)
- 11.11.2026 - Added tests for normalisation, comparison and evaluation (`tests/test_pipeline.py`, applied with AI assistance)
- 22.11.2026 - Added LOC and TIME to the fact normalisation and comparison (`src/normalize.py`, `src/compare.py`, applied with AI assistance)
- 22.11.2026 - Made the comparison take the source article's language, for the Bosnian articles (`src/compare.py`, applied with AI assistance)
- 22.11.2026 - Drafted the pipeline diagram (`docs/pipeline.md`, applied with AI assistance)
