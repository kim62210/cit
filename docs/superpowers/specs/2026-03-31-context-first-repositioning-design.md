# cit Context-First Repositioning Design

## Goal

Reposition `cit` from an account/profile-first product narrative to a context-first narrative without breaking the current command surface, on-disk storage layout, or existing user workflows.

The short-term objective is not to rewrite the system model. It is to make the product explain itself in a way that better matches what the tool already does: manage reusable local Claude working contexts where account identity is only one part of the state.

## Why this change is needed

Today, the repository introduces `cit` as a git-style account switching tool. That framing is directionally true, but it undersells the actual unit of value the product manages.

Current implementation facts:

- `branch` saves a named snapshot that includes Keychain credentials, `oauthAccount`, settings, MCP config, and metadata.
- `checkout` switches more than identity: it applies settings and MCP overrides, auto-stashes unsaved local state, and protects mutation with a file lock and write-ahead log.
- `config` stores per-profile defaults for model, permission mode, and MCP behavior.
- `stash` preserves temporary local switching state.
- `log` exposes session history and usage data adjacent to that local working state.

That means `cit` is already managing a reusable work context, not just an account.

## Product framing

### New product statement

`cit` manages Claude work contexts with a git-like workflow.

### Working definition of context

A context is a reusable local Claude working setup composed of:

- identity and account credentials
- model selection
- permission mode
- MCP defaults
- local switchable state relevant to Claude Code usage

This definition is intentionally narrower than a full workspace abstraction. It does not yet include worktree metadata, project routing, or persistent live session ownership.

## Concept hierarchy

The product should communicate concepts in this order:

1. **Context** — the top-level user mental model
2. **Profile** — a stored context preset or snapshot
3. **Session** — a live or historical run that happens within a context
4. **Account** — one facet of a context

### Rationale

- `profile` already exists in the code and on disk, so it remains the operational storage concept for now.
- `session` is currently observational, not switchable. It should not become the primary concept yet.
- `account` is too narrow because the tool also switches settings, MCP defaults, and local switching state.

## Scope of Phase 1

Phase 1 is a **repositioning pass**, not a structural migration.

### In scope

- README product framing
- CLI help text and command summaries
- package description text
- design document overview and command prose
- output wording where user-facing language clearly reinforces the wrong mental model
- terminology notes that explain the difference between product terms and internal storage terms

### Out of scope

- renaming directories such as `profiles/`
- renaming state keys such as `activeProfile`
- changing the command surface
- introducing new top-level commands
- turning `session` into a switchable or restorable runtime entity
- adding workspace/worktree metadata to the domain model

## Terminology strategy

Phase 1 should intentionally separate **product vocabulary** from **storage vocabulary**.

### Product vocabulary

- Use `context` as the primary term in README, help text, and conceptual explanations.
- Use `account` only when talking about identity fields, billing tier, or Keychain-backed credentials.
- Use `session` only when describing runtime history and usage records.

### Storage and compatibility vocabulary

- Keep `profile` as the implementation/storage term for now.
- Explain that a profile is the current storage form of a saved context.
- Do not hide this distinction. Document it clearly.

### Example wording shift

- Old: “Save current account as a named profile.”
- New: “Save the current Claude context as a reusable named profile.”

## Command model evolution

Phase 1 keeps the commands, but changes how they are described.

### `cit branch`

Current user reading:
- save or delete account profiles

Phase 1 reading:
- save, inspect, and manage reusable Claude contexts stored as named profiles

### `cit checkout`

Current user reading:
- switch to a saved profile/account

Phase 1 reading:
- switch the active Claude work context

### `cit status`

Current user reading:
- print current account state

Phase 1 reading:
- print the active Claude context summary, including identity details

### `cit config`

Current user reading:
- manage per-profile defaults

Phase 1 reading:
- manage global and per-context defaults, currently stored on profile entries

### `cit stash`

Current user reading:
- save temporary account state

Phase 1 reading:
- temporarily shelve and restore the current context state

### `cit log`

Current user reading:
- inspect session usage history

Phase 1 reading:
- inspect session activity associated with local Claude usage; session remains a secondary concept in this phase

## Documentation plan

### README changes

The README should shift from “account switching” to “context switching” while staying honest about the implementation.

Required changes:

- Update the hero statement and subheading
- Reframe the “Why” section around local Claude work contexts
- Reword highlights so account is no longer the center of the story
- Add a short terminology note explaining: context = product term, profile = current stored preset
- Update command descriptions and examples to use context-first language
- Keep dry-run, WAL, lock, stash, and MCP merge as proof that this is more than identity switching

### CLI help changes

Required changes:

- top-level `cit --help` one-line description
- short help for `branch`, `checkout`, `status`, `config`, `stash`, `log`
- quick-start copy in the main help screen

### Design document changes

Required changes:

- update project overview wording
- update motivation so the problem statement includes work contexts, not only accounts
- adjust command descriptions to match the new narrative
- add a terminology section clarifying `context`, `profile`, `session`, and `account`

## Output and UX changes

Phase 1 should be conservative about runtime output changes.

### Safe to change

- help text
- README examples
- docs examples
- selected status labels if they clearly improve product coherence

### Avoid for now

- sweeping output wording changes that might confuse existing users
- renaming every visible `profile` occurrence without explaining compatibility
- introducing terms like `workspace` or `tree` before the product actually manages them

## Migration safety rules

To avoid misleading users, Phase 1 must obey these rules:

1. Never imply that sessions are currently first-class switchable objects.
2. Never imply that profiles have been renamed on disk.
3. Never imply that `cit` manages project worktrees or filesystem trees today.
4. Keep all existing command names valid and documented.
5. Make the context-first story additive, not revisionist.

## Risks

### Risk 1: Narrative outruns the code

If the docs call everything a context manager but outputs and internal names still feel strongly profile/account-centric, users may become more confused rather than less.

Mitigation:

- explicitly document the context/profile distinction
- update the highest-traffic user-facing text first
- avoid overselling session/workspace support

### Risk 2: Session language is promoted too early

External tools like tmux and zellij make `session` feel natural because sessions are persistent, attachable, and resumable. `cit` does not currently manage sessions that way.

Mitigation:

- keep `session` secondary in Phase 1
- reserve session-first naming for a future model change only if the product truly grows there

### Risk 3: Git metaphor becomes semantically muddy

`branch` and `checkout` still sound like a branch-oriented storage model, even if the product is reframed as contexts.

Mitigation:

- preserve the git metaphor but define branch/profile as the stored form of a context
- re-evaluate the command surface only in a later phase

## Follow-up phases

### Phase 2 — Boundary normalization

- add explicit terminology documentation everywhere
- tune status and dry-run output to reinforce context framing
- rename examples, fixture text, and help examples for consistency

### Phase 3 — Internal model evaluation

- decide whether `profiles/` should become `contexts/`
- decide whether `activeProfile` should become `activeContext`
- determine whether on-disk migration is worth the compatibility cost

### Phase 4 — Session-aware product expansion

Only consider after the product actually manages live session behavior.

Potential future work:

- attach/resume semantics
- context-to-session mapping
- project-bound context state
- richer session trees or navigation concepts

## Success criteria

Phase 1 is successful when:

- a new reader understands `cit` as a Claude context manager, not just an account switcher
- the README, CLI help, and design document all reinforce the same concept hierarchy
- existing users can keep using the same commands without any migration
- no documentation promise exceeds what the code currently does

## Open questions

- Should `profile` remain visible in user-facing output indefinitely, or only as a documented implementation term?
- Should `status` lead with “Context” even before any state key changes happen?
- When the product eventually grows workspace awareness, should that become part of `context`, or a separate peer concept?
- At what point would a command surface alias such as `cit context ...` become worth introducing?

## Recommendation

Proceed with Phase 1 immediately.

This is the highest-leverage change with the lowest implementation risk. It improves the product narrative, better matches the current code reality, and keeps future doors open for richer context and session models without forcing an early schema migration.
