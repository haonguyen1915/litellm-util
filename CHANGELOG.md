# Changelog

## [0.2.3] - 2026-03-20

### Release Notes

### What's Changed
- Fixed issue with team daily activity reporting by ensuring all pages are fetched, preventing data underreporting.

### Bug Fixes

- fix: fetch all pages in team daily activity to prevent underreporting (c6cb359)

**Contributors:** @haonguyen

**Compare changes:** [v0.2.2...v0.2.3](https://github.com/haonguyen1915/litellm-util.git/-/compare/v0.2.2...v0.2.3)

## [0.2.2] - 2026-03-18

### Release Notes

Minor maintenance update with no user-facing changes.

### What's Changed
- Updated API key for improved backend integration.

**Contributors:** @haonguyen

**Compare changes:** [v0.2.1...v0.2.2](https://github.com/haonguyen1915/litellm-util.git/-/compare/v0.2.1...v0.2.2)

## [0.2.1] - 2026-03-18

### Release Notes

Enhanced CLI functionality with new features and improved usability.

### What's Changed
- Introduced a new usage API to track spend and usage statistics effectively.
- Expanded --last options for more flexible date filtering in team commands.
- Added support for updating virtual keys with new aliases and team assignments.
- Enabled model management from file for streamlined operations.
- Implemented command history tracking for better user experience.

### Features

- feat: expand --last options and add date filtering to by-team (2d5f4fb)
- feat: add usage API (13ccbcb)
- feat: add examples (ced32f1)
- feat: prevent doupble key (7bbc3e6)
- feat: add key update (38a7009)
- feat: allow add model from file (cc40320)
- feat: add API team get (4575f7f)
- feat: add history (013a633)
- feat: add rotate master key (6bf1394)
- feat: init code base (51c3d0f)

**Contributors:** @haonguyen, @Nguyễn Văn Hảo

