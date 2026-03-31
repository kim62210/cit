# cit Repository Agent Rules

## Mandatory Repository Language

- Write all repository content in English.
- Never write commit messages in Korean for this repository.
- Never write repository documentation, comments, tests, or CLI text in Korean for this repository.

## Scope of "Repository Content"

This includes, but is not limited to:

- commit messages
- branch names
- pull request titles and descriptions
- README and docs files
- code comments and docstrings
- test names and fixture text
- CLI help, terminal output, and error messages
- planning notes or implementation notes stored in the repository

## Enforcement

- Prefer English even when the user speaks Korean.
- If you are about to write non-English repository text, stop and rewrite it in English first.
- When updating prior content, normalize touched text to English unless it must remain unchanged because it is external or quoted content.
- Maintain at least 80% total test coverage for the `cit` package.
- Run coverage-enforced tests before claiming implementation work is complete.
