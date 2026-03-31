# Phase 1 Context-First Repositioning Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reposition `cit` from an account/profile-first narrative to a context-first narrative without breaking commands, storage layout, or existing user workflows.

**Architecture:** This plan changes product-facing language first and leaves the internal storage model intact. The work is intentionally split into documentation, CLI help text, and selected runtime wording so the public narrative becomes context-first while `profile` remains the implementation/storage term for compatibility.

**Tech Stack:** Python 3.12+, Click, pytest, Markdown, Mermaid.

---

## File map

### Product and documentation surface

- Modify: `README.md`
- Modify: `docs/DESIGN.md`
- Modify: `pyproject.toml`
- Modify: `CHANGELOG.md`

### CLI help and runtime wording

- Modify: `cit/cli.py`
- Modify: `cit/commands/branch.py`
- Modify: `cit/commands/checkout.py`
- Modify: `cit/commands/status.py`
- Modify: `cit/commands/config.py`
- Modify: `cit/commands/stash.py`
- Modify: `cit/commands/log.py`

### Tests

- Modify: `tests/test_cli_help.py`
- Modify: `tests/test_status.py`
- Create or modify: `tests/test_context_framing.py` (only if needed to keep wording assertions isolated)

### Non-goals for this plan

- Do **not** rename `profiles/` to `contexts/`
- Do **not** rename `activeProfile` or `previousProfile`
- Do **not** add new top-level commands
- Do **not** introduce new persistence fields or schema migrations

---

## Task 1: Reposition the top-level product narrative

**Files:**
- Modify: `README.md`
- Modify: `pyproject.toml:5-20`
- Modify: `CHANGELOG.md`

- [ ] **Step 1: Write the failing documentation-oriented tests or assertions first**

If the repo already tests help or visible copy, extend those tests first before editing docs/help text. If no direct README tests exist, skip README assertions and anchor the red step in CLI help tests from Task 2.

- [ ] **Step 2: Update the package description**

Change the package description in `pyproject.toml` from account-centric wording to context-centric wording.

Recommended direction:

```toml
description = "A git-style CLI for managing Claude work contexts"
```

- [ ] **Step 3: Rewrite the README hero and Why section**

Update these parts so they describe `cit` as a Claude work context manager.

Required changes:
- Hero statement uses `context` as the top-level term
- “Why” section explains that identity is only one part of a Claude work context
- Add a terminology note explaining `context` vs stored `profile`

- [ ] **Step 4: Update command descriptions in the README**

Revise the command map and quick-start prose so:
- `branch` saves reusable Claude contexts stored as named profiles
- `checkout` switches the active context
- `status` summarizes the active context, including identity details
- `stash` shelves temporary context state
- `log` remains session-oriented and secondary

- [ ] **Step 5: Update CHANGELOG.md**

Add a new `Unreleased` entry describing the context-first documentation/wording shift once the actual implementation changes are made.

- [ ] **Step 6: Verify docs read cleanly**

Read the changed sections in full and confirm they do not promise any unsupported behavior like session switching, worktree management, or renamed on-disk structures.

---

## Task 2: Reframe the CLI help surface

**Files:**
- Modify: `cit/cli.py`
- Modify: `cit/commands/branch.py`
- Modify: `cit/commands/checkout.py`
- Modify: `cit/commands/status.py`
- Modify: `cit/commands/config.py`
- Modify: `cit/commands/stash.py`
- Modify: `cit/commands/log.py`
- Modify: `tests/test_cli_help.py`

- [ ] **Step 1: Write the failing help-output test**

Extend `tests/test_cli_help.py` so it fails against the current wording.

Add assertions for phrases like:

```python
assert "Claude work contexts" in result.output
assert "stored as named profiles" in result.output
assert "active context" in result.output
```

- [ ] **Step 2: Run the targeted help test to verify it fails**

Run:

```bash
./.venv/bin/pytest tests/test_cli_help.py -q -o addopts='-q'
```

Expected: FAIL because existing help text still talks about accounts/profiles first.

- [ ] **Step 3: Update the top-level help framing**

Edit `cit/cli.py`:
- Change `HELP_SUMMARY`
- Change `HELP_DETAILS`
- Change `QUICK_START`

Recommended direction:
- summary: `Git-style context switching for Claude Code.`
- details: explain reusable contexts where identity is one part of the state
- quick start: mention context explicitly without hiding the stored-profile term

- [ ] **Step 4: Update command `help` and `short_help` strings**

Edit each top-level command so wording becomes context-first while staying honest:

- `branch`: “save, list, and remove named Claude contexts stored as profiles”
- `checkout`: “switch the active Claude work context”
- `status`: “show the active context summary”
- `config`: “manage global and per-context defaults”
- `stash`: “temporarily save and restore context state”
- `log`: keep session history wording, but avoid implying sessions are the primary object

- [ ] **Step 5: Re-run the targeted help test**

Run:

```bash
./.venv/bin/pytest tests/test_cli_help.py -q -o addopts='-q'
```

Expected: PASS.

---

## Task 3: Adjust selected runtime wording without breaking compatibility

**Files:**
- Modify: `cit/commands/status.py`
- Modify: `cit/commands/checkout.py`
- Modify: `tests/test_status.py`

- [ ] **Step 1: Write a failing status-output test**

Extend `tests/test_status.py` with a context-first wording assertion.

Recommended minimal target:

```python
assert "Context:" in result.output
assert "Profile:" in result.output or "Stored Profile:" in result.output
```

Only do this if you are intentionally changing runtime output labels in Phase 1. If that proves too risky, document in the code review notes that runtime output remains unchanged in this phase.

- [ ] **Step 2: Decide the runtime wording boundary**

Pick one of these and stay consistent:

1. Conservative: change only help/docs, keep runtime output stable
2. Moderate: add a top-line `Context:` label while preserving `Profile:` and `Account:` detail labels

Recommended: option 2 only if tests remain readable and the output still feels unsurprising.

- [ ] **Step 3: Update dry-run wording if needed**

If `checkout --dry-run` is changed, prefer light-touch wording such as:

```text
Dry run: switch context 'work'
Stored profile: personal -> work
Account: active@example.com -> work@example.com
```

Do **not** remove `profile` completely from the preview if it is still the actual stored entity.

- [ ] **Step 4: Run the targeted status/checkout tests**

Run:

```bash
./.venv/bin/pytest tests/test_status.py tests/test_checkout.py -q -o addopts='-q'
```

Expected: PASS.

---

## Task 4: Reframe the formal design document

**Files:**
- Modify: `docs/DESIGN.md`

- [ ] **Step 1: Update the overview and motivation sections**

Change the framing from “account switching” to “context switching” without lying about the implementation.

Required updates:
- title/subtitle language
- “What is cit?”
- “Motivation” wording

- [ ] **Step 2: Add an explicit terminology section**

Insert a short section near the overview or architecture chapters defining:

- Context
- Profile
- Session
- Account

The key sentence should be that a profile is the current stored form of a context.

- [ ] **Step 3: Update command prose**

Touch the prose around `branch`, `checkout`, `status`, `config`, `stash`, and `log` so it matches the Phase 1 concept hierarchy.

- [ ] **Step 4: Keep architecture and on-disk structure accurate**

Do not rename:
- `profiles/`
- `activeProfile`
- `previousProfile`

If needed, add a note clarifying that these are current implementation terms.

---

## Task 5: Full verification and shipping prep

**Files:**
- Verify: all changed files from Tasks 1–4

- [ ] **Step 1: Run the full suite with coverage enforcement**

Run:

```bash
./.venv/bin/pytest
```

Expected: PASS with total coverage still at or above 80%.

- [ ] **Step 2: Check Python diagnostics**

Run LSP diagnostics or the equivalent project diagnostic check across the repository.

Expected: 0 errors.

- [ ] **Step 3: Manually inspect CLI help**

Run:

```bash
./.venv/bin/cit --help
./.venv/bin/cit checkout --help
./.venv/bin/cit status --help
```

Expected: wording is context-first, readable, and still truthful.

- [ ] **Step 4: Review the docs for unsupported promises**

Specifically verify the changed docs do **not** claim:
- session attach/resume support
- workspace or worktree management
- renamed storage directories or keys

- [ ] **Step 5: Commit in one documentation/wording-focused change set**

Suggested message:

```bash
git add README.md docs/DESIGN.md pyproject.toml CHANGELOG.md cit/cli.py cit/commands/*.py tests/test_cli_help.py tests/test_status.py
git commit -m "docs: reposition cit around Claude work contexts"
```

If runtime wording changes are substantial enough, split into:

1. `docs: reposition cit around Claude work contexts`
2. `feat: update CLI wording for context-first framing`

---

## Execution notes

- Favor wording changes over structural changes.
- If any planned change makes runtime terminology less clear for current users, revert to the more conservative Phase 1 wording.
- Do not let the narrative get ahead of the implementation.

## Done criteria

This plan is complete when:

- `cit` reads as a context manager across README, help text, and design docs
- `profile` is still clearly acknowledged as the current storage term
- the command surface remains unchanged
- tests and coverage still pass
- no new unsupported concept is introduced by wording alone
