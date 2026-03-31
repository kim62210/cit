# cit

`cit` is a git-style CLI for managing local Claude Code accounts and profiles on macOS.

## Commands

- `cit branch`
- `cit checkout`
- `cit status`
- `cit config`
- `cit stash`
- `cit log`

## Development

```bash
python3 -m venv .venv
./.venv/bin/python -m pip install -e ".[dev]"
./.venv/bin/pytest
```

## Test Coverage Policy

- The repository must maintain at least 80% total test coverage for the `cit` package.
- Use `./.venv/bin/pytest` to run the suite with coverage enforcement.
