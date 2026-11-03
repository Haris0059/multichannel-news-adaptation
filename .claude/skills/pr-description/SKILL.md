---
name: pr-description
description: Write a pull request title and description. Use when creating a PR, writing a PR, or when the user asks to summarize a branch's changes for a pull request.
---

# PR descriptions

Read the whole branch before writing: `git log <base>..HEAD --format=%s` and `git diff <base>...HEAD`. The base is the repo's default branch (`gh repo view --json defaultBranchRef -q .defaultBranchRef.name`), not always `main`. Write from the diff and commits, not from memory of the conversation.

## Title

Short imperative sentence, all lowercase (same as commit messages), no prefix, no trailing period. Follow the repo's convention if CLAUDE.md sets one.

## Body

```
## What
One or two sentences: what this PR does, in terms of behavior.

## Why
The problem or context that made it necessary, and any non-obvious decision (why this approach, what was left out on purpose).

## Changes
- Specific changes, grouped by area (e.g. **Frontend** / **Backend**), naming the files or functions that matter.
- Call out deletions, renames, migrations, new env vars and config.

## Testing
- Exact commands that verify it, taken from the repo's CI and CLAUDE.md, not invented.
- Manual steps with expected results, if the change is visible or behavioral.
```

## Rules

- Be concrete and concise: what a reviewer needs to review it, nothing they can read off the diff line by line.
- Only claim tests you saw pass or can point to. If something wasn't run, say so.
- Skip a section that has nothing to say instead of padding it (a "No files deleted" line is fine, an empty heading is not).
- No attribution lines ("Generated with Claude Code" and the like).
- Write the body to a file or pass it via `--body-file`/heredoc so markdown survives; create the PR with `gh pr create` only when asked, and never push or merge unasked.
