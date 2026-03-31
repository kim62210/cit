# Changelog

All notable changes to this project will be documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project currently tracks work ahead of formal tagged releases.

## [Unreleased]

### Added

- Added a custom block-style ASCII hero banner to the main CLI help screen.
- Added `cit checkout --dry-run` to preview account, settings, MCP, auto-stash, and warning changes before applying a switch.
- Added regression coverage for CLI help output and dry-run preview behavior.

### Changed

- Refined the main `cit --help` experience with clearer command summaries and quick-start examples.
- Improved checkout planning so the same switch computation can drive both preview output and real execution.

## [0.1.0] - 2026-03-31

### Added

- Added the initial `cit` Python CLI scaffold with `click` command registration and package metadata.
- Added top-level commands for `branch`, `checkout`, `status`, `config`, `stash`, and `log`.
- Added profile snapshot storage for Keychain credentials, Claude account metadata, settings, and MCP configuration.
- Added session usage parsing and estimated token cost reporting from local Claude JSONL session files.
- Added repository-level English authoring rules and coverage enforcement for the `cit` package.

### Changed

- Added branded command help text and quick-start guidance for the CLI experience.
- Added support for applying profile-scoped `model`, `permission-mode`, and `mcp.<server>` overrides during checkout.

### Fixed

- Improved WAL recovery and locking consistency around state mutations.
- Tightened snapshot directory and keychain file permissions.
- Added a warning when checkout runs while a Claude process appears to be active.

### Security

- Enforced private filesystem permissions for profile and stash snapshots.
- Preserved atomic switching behavior with a write-ahead log and startup recovery path.
