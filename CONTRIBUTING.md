# Contributing

Thank you for helping improve Multica Best Practices.

## What we welcome

- Clearer templates (Agent / Squad / Skill / Issue Instructions)
- Desensitized real case studies (into `docs/` or the matching Starter)
- Stack-specific verification command tables (Node, Go, Python, etc.)
- Fixes to outdated Multica behavior descriptions (cite official docs or versions)
- Translations (the repository is English-only; translations live in forks)

## What to avoid

- Hardcoded workspace IDs, tokens, or private URLs
- Claiming a single "correct" agent count for everyone
- Replacing Multica product docs — link to the official docs instead
- Large binaries without good reason

## How to contribute

1. Branch from `main`.
2. Keep changes focused (one Starter or one doc topic per PR).
3. Add a short entry to `CHANGELOG.md`.
4. Describe in the PR:
   - What problem it solves
   - How it was verified (even "doc review")
   - Any Multica version assumptions

## Template style

- Prefer directly copyable Markdown code blocks.
- Agent templates state **responsibilities / prohibitions / delivery format**.
- Mark optional content explicitly.
- Avoid assuming a single model vendor.

## Starter style

- `templates/en_US/squad/software-development` is the repo MVP; changes must keep it copy-paste-run.
- Ship "why it works" and "common failure modes" next to each template.
- Validate new starters on real tasks before submitting (see the README contribution bar: problem / scenarios / complete template / real example / known failure cases).
