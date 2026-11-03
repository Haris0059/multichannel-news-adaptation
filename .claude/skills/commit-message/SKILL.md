---
name: commit-message
description: Write the git commit message whenever committing, or when the user says "commit", "stage and commit", "push changes", or asks to save or finalize changes. Use before every `git commit`.
---

# Commit messages

Before committing, run `git diff --staged` (and `git log -5 --format=%s` to match the repo's style) and write the message from what is actually staged.

## Format

- One line only: no body, no trailer, no trailing period.
- Imperative, all lowercase, no prefix (`add`, `fix`, `remove`, `rename`). No `feat:`/`fix:` tags.
- Aim for under 50 characters, hard cap 72.
- Say what changed in concrete terms. Name the thing: `add article-level train/val/test split`, not `update data`.

## Rules

- No attribution: no "Generated with Claude Code", no `Co-Authored-By` lines.
- No vague messages ("Update files", "Fix issues", "Misc changes").
- If the staged diff mixes unrelated changes, say so and suggest splitting it into separate commits instead of writing an "and" message.
- If the repo's CLAUDE.md sets a different commit convention, follow that; it overrides this file.
- Run the `ai-log` skill first so `docs/AI_LOG.md` lands in the same commit.
- Commit only when the user asked for a commit. Never push unless asked.
