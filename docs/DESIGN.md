# cit — Design Specification v1.0

> **cit** (Claude + git) — A git-style CLI for managing Claude work contexts

## 1. Project Overview

### 1.1 What is cit?

`cit` is a command-line tool for managing reusable Claude work contexts on a single machine. It borrows git's mental model — branches, checkout, stash — to make context switching feel natural to developers who already think in git terms. In the current implementation, saved contexts are stored as named profiles.

### 1.2 Motivation

Claude Code stores exactly one active work context across three distinct locations:

| Location | What it stores |
|----------|---------------|
| macOS Keychain (`Claude Code-credentials`, account=`whoami`) | OAuth tokens, subscriptionType, rateLimitTier, scopes, expiry |
| `~/.claude.json` → `oauthAccount` field | accountUuid, emailAddress, organizationUuid, displayName, billingType, orgRole |
| `~/.claude/settings.json` | model preference, hooks, plugins, MCP servers (shared across accounts today) |

Switching between a personal Max subscription and a work Team subscription requires manually exporting/importing Keychain entries and editing JSON files. `cit` automates this as part of a broader local context switching workflow.

### 1.2.1 Terminology

- **Context** — the top-level product concept; a reusable Claude working setup
- **Profile** — the current stored form of a saved context on disk
- **Session** — a live or historical Claude run associated with local usage
- **Account** — one identity facet within a context

### 1.3 Non-Goals (MVP)

- No GUI or TUI beyond styled terminal output
- No credential encryption beyond macOS Keychain (the OS handles it)
- No network calls to Anthropic APIs (pure local file manipulation)
- No modification of Claude Code's own source or binary
- No Windows/Linux support in v1 (Keychain-specific)

---

## 2. Command Reference

### 2.1 `cit branch`

List, create, and delete named profiles that store reusable Claude contexts.

```bash
cit branch                     # List all profiles (* = active)
cit branch <name>              # Save current active account as <name>
cit branch -d <name>           # Delete profile
cit branch -v                  # Verbose: show email, org, subscription, rateLimitTier
```

**Output example:**
```
  personal          brian@gmail.com         max (20x)
* work              kim.hyung.joo@drb.com   team
  freelance         brian@freelance.io       pro
```

**Implementation details:**
- `cit branch <name>` snapshots: Keychain JSON, `oauthAccount` from `~/.claude.json`, and optionally `~/.claude/settings.json` (if `--with-config` flag).
- Profile name validation: `[a-z0-9][a-z0-9_-]*`, max 32 chars.
- Name `HEAD` is reserved (used internally to track active profile).

### 2.2 `cit checkout <name>`

Switch to a saved Claude context stored as a profile.

```bash
cit checkout <name>            # Switch to profile
cit checkout -b <name>         # Create profile from current state + switch
cit checkout -                 # Switch to previous profile (like `cd -`)
```

**Switching procedure (atomic):**
1. Read target profile from `~/.cit/profiles/<name>/`
2. Validate Keychain access (prompt user if locked)
3. If current state is unsaved, auto-stash with message `auto: pre-checkout from <current>`
4. Write Keychain: `security delete-generic-password` then `security add-generic-password`
5. Patch `~/.claude.json` → replace `oauthAccount` field (preserve all other fields)
6. If profile has config overrides, merge into `~/.claude/settings.json`
7. Update `~/.cit/state.json` → `activeProfile`, `previousProfile`
8. Print confirmation with profile summary

**Atomicity:** Steps 4-6 use a write-ahead log (`~/.cit/wal.json`). If any step fails, the WAL is replayed in reverse on next `cit` invocation. This prevents half-switched states.

### 2.3 `cit status`

Display the active context summary, including account identity details.

```bash
cit status                     # Full status
cit status --short             # One-line summary
```

**Output example:**
```
Profile:       work
Account:       kim.hyung.joo@drbworld.com
Display Name:  brian
Organization:  kim.hyung.joo@drbworld.com's Organization (admin)
Subscription:  max (rateLimitTier: default_claude_max_20x)
Model:         opus[1m]
Token Expiry:  2026-04-07 09:44:01 (6d 22h remaining)

Session:       active (PID 8bf66553)
Stash:         1 entry
```

**Data sources:**
- `subscriptionType`, `rateLimitTier`: Keychain → `claudeAiOauth`
- `emailAddress`, `displayName`, `organizationName`, `organizationRole`: `~/.claude.json` → `oauthAccount`
- `model`: `~/.claude/settings.json` → `model`
- Token expiry: `claudeAiOauth.expiresAt` (epoch ms) from Keychain
- Stash count: entries in `~/.cit/stash/`

### 2.4 `cit config`

Per-context and global configuration.

```bash
cit config <key> <value>           # Set for current profile
cit config <key>                   # Get value
cit config --list                  # List all config for current profile
cit config --global <key> <value>  # Set global default
cit config --unset <key>           # Remove key from current profile
```

**Supported keys (MVP):**

| Key | Type | Description | Applied to |
|-----|------|-------------|-----------|
| `model` | string | Default model (e.g., `opus`, `sonnet`) | `~/.claude/settings.json` → `model` |
| `permission-mode` | string | Permission behavior | `~/.claude/settings.json` |
| `auto-stash` | bool | Auto-stash on checkout (default: true) | `cit` behavior only |
| `mcp.<server>` | JSON | MCP server config to apply on checkout | `~/.claude/.mcp.json` |

**Resolution order (lowest → highest priority):**
1. Built-in defaults
2. `~/.cit/config.toml` → `[global]`
3. `~/.cit/config.toml` → `[profile.<name>]`
4. Command-line flags

### 2.5 `cit stash` / `cit stash pop`

Temporarily save and restore context state.

```bash
cit stash                       # Push current state onto stash stack
cit stash pop                   # Restore most recent stash + remove it
cit stash list                  # Show stash stack
cit stash drop [<index>]        # Remove stash entry without applying
cit stash show [<index>]        # Show stash entry details
```

**Output example (`cit stash list`):**
```
stash@{0}: work - kim.hyung.joo@drbworld.com (max) [2m ago]
stash@{1}: auto: pre-checkout from personal [1h ago]
```

**Implementation:** Each stash entry is a directory under `~/.cit/stash/<timestamp>/` containing the same files as a profile snapshot. Stack order maintained in `~/.cit/state.json` → `stashStack[]`.

### 2.6 `cit log`

Session history with token usage, shown alongside local context workflows.

```bash
cit log                         # Recent sessions (default: last 20)
cit log --today                 # Today's sessions only
cit log --week                  # This week's sessions
cit log --project [<path>]      # Filter by project (default: cwd)
cit log --stats                 # Aggregate token counts + estimated cost
cit log --json                  # Machine-readable output
```

**Output example:**
```
2026-03-31  local-agent  main
  8bf66553  10:55  claude-opus-4-6  in:23,269  out:131  cache_read:10,482

2026-03-30  deep-research  feature/auto-curate
  8ce7f84f  14:55  claude-opus-4-6  in:45,102  out:892  cache_read:22,541

── Today: 2 sessions, 68,371 input tokens, 1,023 output tokens ──
── Est. cost: $1.07 (at opus $15/M input, $75/M output) ──
```

**Data source:** `~/.claude/projects/<project-slug>/<session-id>.jsonl` — each assistant message line contains `message.usage` with `input_tokens`, `output_tokens`, `cache_creation_input_tokens`, `cache_read_input_tokens`.

---

## 3. Architecture

### 3.1 Directory Structure

```
~/.cit/
  state.json              # Active profile, previous profile, stash stack pointer
  config.toml             # Global + per-profile config
  wal.json                # Write-ahead log for atomic switches (empty when clean)
  .lock                   # File lock for concurrent access prevention
  profiles/
    <name>/
      keychain.json       # Snapshot of Keychain claudeAiOauth JSON
      oauth_account.json  # Snapshot of ~/.claude.json oauthAccount field
      settings.json       # Optional: settings snapshot
      mcp.json            # Optional: MCP server config snapshot
      meta.json           # Created timestamp, last-used timestamp, source email
  stash/
    <timestamp>/
      (same structure as profiles/<name>/)
```

### 3.2 State File

```json
{
  "version": 1,
  "activeProfile": "work",
  "previousProfile": "personal",
  "stashStack": ["1774850112995", "1774843200000"],
  "lastSwitchedAt": 1774850112995
}
```

### 3.3 Config File

```toml
[global]
auto-stash = true

[profile.work]
model = "opus[1m]"
permission-mode = "dangerousSkipPermissions"

[profile.personal]
model = "opus"

[profile.personal.mcp.memory]
command = "npx"
args = ["@anthropic/memory-mcp"]
```

### 3.4 Data Flow: `cit checkout work`

```
 1. Read ~/.cit/state.json → activeProfile = "personal"
 2. auto-stash = true? → snapshot current state to ~/.cit/stash/<ts>/
 3. Read ~/.cit/profiles/work/keychain.json
 4. Write WAL: { op: "checkout", from: "personal", to: "work", step: 0 }
 5. security delete-generic-password → security add-generic-password
 6. WAL step: 1
 7. Patch ~/.claude.json → oauthAccount = profiles/work/oauth_account.json
 8. WAL step: 2
 9. Merge profiles/work/settings.json → ~/.claude/settings.json (if exists)
10. WAL step: 3
11. Merge profiles/work/mcp.json → ~/.claude/.mcp.json (if exists)
12. Clear WAL
13. Update state.json: activeProfile="work", previousProfile="personal"
```

### 3.5 Package Structure

```
cit/
  __init__.py             # __version__
  cli.py                  # Click group + command registration
  commands/
    branch.py
    checkout.py
    status.py
    config.py
    stash.py
    log.py
  core/
    keychain.py           # macOS Keychain read/write via `security` subprocess
    claude_files.py       # Read/write ~/.claude.json, settings.json, .mcp.json
    profile.py            # Profile CRUD (save, load, delete, list)
    state.py              # state.json management
    config_manager.py     # config.toml read/write with resolution order
    wal.py                # Write-ahead log for atomic switches
    session_reader.py     # Parse session JSONL for cit log
    pricing.py            # Token cost estimation table
  platform/
    macos.py              # macOS Keychain implementation
    base.py               # Abstract CredentialStore protocol
  models/
    profile.py            # Pydantic: Profile, KeychainData, OAuthAccount
    session.py            # Pydantic: SessionEntry, TokenUsage
    config.py             # Pydantic: CitConfig, ProfileConfig
pyproject.toml
README.md
LICENSE
tests/
  conftest.py
  test_branch.py
  test_checkout.py
  test_status.py
  test_config.py
  test_stash.py
  test_log.py
  test_keychain.py
  test_wal.py
  fixtures/
```

### 3.6 Dependencies

| Package | Purpose |
|---------|---------|
| `click>=8.1` | CLI framework |
| `rich>=13.9` | Styled terminal output |
| `pydantic>=2.9` | Data validation |
| `tomli-w>=1.0` | TOML write (read via stdlib `tomllib`) |

---

## 4. Discovered Data Structures

Actual structures found on the machine, forming the source-of-truth.

### 4.1 macOS Keychain Entry

```json
{
  "claudeAiOauth": {
    "accessToken": "sk-ant-oat01-...",
    "refreshToken": "sk-ant-ort01-...",
    "expiresAt": 1774945441271,
    "scopes": ["user:inference", "user:sessions:claude_code", "..."],
    "subscriptionType": "max",
    "rateLimitTier": "default_claude_max_20x"
  }
}
```

### 4.2 `~/.claude.json` → `oauthAccount`

```json
{
  "accountUuid": "b54e9bdf-...",
  "emailAddress": "kim.hyung.joo@drbworld.com",
  "organizationUuid": "20dd6f68-...",
  "displayName": "brian",
  "organizationRole": "admin",
  "organizationName": "kim.hyung.joo@drbworld.com's Organization",
  "billingType": "stripe_subscription",
  "subscriptionCreatedAt": "2026-03-11T23:53:53.369964Z"
}
```

Note: `subscriptionType` lives only in the Keychain's `claudeAiOauth`, NOT in `oauthAccount`.

---

## 5. Security Considerations

- **File permissions:** `~/.cit/` is `0700`, all `keychain.json` files are `0600`
- **Token redaction:** Logger output redacts tokens to `sk-ant-***<last4>`
- **No token refresh:** `cit` does not refresh tokens. Claude Code handles this on launch
- **Concurrency:** File lock (`~/.cit/.lock`) via `fcntl.flock()` prevents concurrent mutation
- **Running Claude warning:** `cit checkout` warns if `claude` process is detected via `pgrep`
- **JSON preservation:** Only `oauthAccount` key is patched in `~/.claude.json`; all other fields preserved

---

## 6. Platform Support Strategy

| Version | Platform | Credential Backend |
|---------|----------|--------------------|
| v1 | macOS | `security` CLI (Keychain) |
| v2 | Linux | `libsecret` (GNOME Keyring) or file fallback |
| v2 | Windows | `wincred` via `keyring` package |

All Keychain operations are behind a `CredentialStore` protocol for easy extension.

---

## 7. Future Roadmap (v2+)

| Command | Purpose |
|---------|---------|
| `cit diff <a> <b>` | Show differences between two profiles |
| `cit gc` | Clean up expired tokens, orphaned stash entries |
| `cit tag` | Alias profiles for short names |
| `cit remote` | Link to Anthropic API for token refresh |
| `cit reset` | Restore Claude Code to factory defaults |
| `cit export` / `cit import` | Portable profile bundles (encrypted) |
| `cit hook` | Pre/post-checkout hooks |
| `cit completions` | Shell completions for bash/zsh/fish |
| Linux + Windows | `libsecret` and `wincred` backends |

---

## 8. Build & Distribution

```toml
[project]
name = "cit-cli"
requires-python = ">=3.12"
dependencies = ["click>=8.1", "rich>=13.9", "pydantic>=2.9", "tomli-w>=1.0"]

[project.scripts]
cit = "cit.cli:main"
```

- PyPI: `pip install cit-cli`
- Homebrew tap: `brew install <user>/tap/cit`
- uv: `uv tool install cit-cli`
