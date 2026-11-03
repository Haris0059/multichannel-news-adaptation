# AI Usage Log

Record of AI tool usage in this project. One row per use, newest last.

| Date | Member | Tool | Where | How | Result |
|------|--------|------|-------|-----|--------|
| 24.10.2026 | Haris Skeledžija | Claude Code (Claude Opus 5.5) | `.claude/skills/ai-log/SKILL.md`, `docs/AI_LOG.md` | Set up a project skill that logs AI use per use and before commits | Reviewed the skill; requested the course table format, per-use logging, and removal of the no-AI rule |
| 24.10.2026 | Haris Skeledžija | Codex (GPT-6.1 Sol) | `.agents/skills/ai-log/SKILL.md` | Created a Codex version of the ai-log skill | Reviewed by Haris before commit |
| 24.10.2026 | Fadil Masnopita | Sonnet 5.5 | in app| Used it to divide the work as best as possible  | Reviewed by Fadil before commit |
| 03.11.2026 | Haris Skeledžija | Claude Code (Claude Opus 5.5) | `src/clean.py` | Changed the script to read the newest raw file in `data/raw/` (`max` over `glob`) instead of a hard-coded date | Chose this option after comparing alternatives; ran the script, 166 articles saved |
| 03.11.2026 | Haris Skeledžija | Claude Code (Claude Opus 5.5) | `.claude/skills/commit-message/`, `.claude/skills/pr-description/`, `.claude/skills/i-have-adhd/`, `.claude/settings.json` | Added commit-message and pr-description skills adapted to lowercase style, and the i-have-adhd skill with a SessionStart hook so it is always on for the team | Haris chose to make i-have-adhd mandatory for the team; reviewed the skill diffs before commit |
| 03.11.2026 | Fadil Masnopita | Claude Code (Claude Opus 5.5) | `docs/labelling_rules.md` | Drafted the labelling rules for PERSON, ORG, DATE and NUMBER with English and Bosnian examples, edge cases and open questions | Committed as draft v0.1; Fadil reviews the span decisions and open questions before the agreement round |
| 03.11.2026 | Fadil Masnopita | Claude Code (Claude Opus 5.5) | `src/split.py` | Found that the script crashes on Windows because it reads `cleaned.jsonl` without `encoding="utf-8"`, and added the encoding | Reran the script; `data/split.json` is unchanged |

