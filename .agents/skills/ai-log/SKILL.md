---
name: ai-log
description: Add a row to docs/AI_LOG.md for each use of AI in this project. Use after any AI-assisted work in this repo (planning, research, drafting, code), and always before every git commit to make sure every use since the last commit is logged. Triggers on "commit", "stage and commit", "push changes", or when the user asks to save or finalize changes.
---

# AI usage log

The course requires one log row per use of AI, not per commit. A "use" is one task the AI helped with: planning, research, drafting text, writing or fixing code.

Resolve the paths below from the repository root, not from this skill's directory.

## Steps

1. After AI-assisted work, add a row to the table in `docs/AI_LOG.md`. Newest row goes last.
2. Before every commit, check that every AI use since the last commit has a row. Add any that are missing.
3. When preparing an authorized commit, run `git add docs/AI_LOG.md` so it lands in the same commit as the work.

## Table format

Use the course's format exactly. The row below is an example, not an actual log entry:

```markdown
| Date | Member | Tool | Where | How | Result |
|------|--------|------|-------|-----|--------|
| 24.10.2026 | Haris Skeledžija | Codex (GPT-6) | `src/scraper.py` | Generated the GraphQL query for articles | Used after testing; fixed pagination by hand |
```

- **Date:** `DD.MM.YYYY`, same as `CONTRIBUTIONS.md`.
- **Member:** full name as written in `CONTRIBUTIONS.md`. Map from `git config user.name`; if unclear, ask.
- **Tool:** AI tool and actual model used. For Codex work, record `Codex (model name)` using the model identified by the current session. If the model is unavailable, ask rather than guessing or copying the example.
- **Where:** the file, document, or project part the AI worked on.
- **How:** what the AI was asked to do, in one sentence.
- **Result:** what was kept, and what the member reviewed, changed, or rejected. Ask the member what they checked; do not guess.

## Rules

- Log only real AI use. If the AI did nothing but run the commit, do not add a row.
- Check existing rows before appending so the same AI use is not logged twice when switching between Claude Code and Codex.
- Be specific and honest. Do not inflate or downplay the AI's part.
- Do not rewrite or delete earlier rows.
