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

## Abdurrahman Beširović
- 06.11.2026 - Wrote the fact normalisation for dates, numbers, names and organisations (`src/normalize.py`, applied with AI assistance)
- 06.11.2026 - Wrote the fact comparison that labels post facts as correct, changed or added (`src/compare.py`, applied with AI assistance)
- 06.11.2026 - Wrote the evaluation script for scores, fact change rates and the error list (`src/evaluate.py`, applied with AI assistance)
