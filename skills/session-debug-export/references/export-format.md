# Session Debug Export References

## Export Layout

- Export root: `<workspace>/.openclaw/trajectory-exports/`
- One run: `<slug>__YYYYMMDD-HHMMSS/`
- Primary files:
  - `report.md`
  - `manifest.json`
  - `events.jsonl`
  - `metadata.json`
  - `prompts.json`
  - `tools.json`
  - `system-prompt.txt`
  - `session-branch.json`

## Suggested Report Sections

1. Session identity
2. Short issue title
3. Export summary counts
4. Important tool errors/fallbacks
5. Recent gateway logs
6. Next debugging step

## Debug Reading Order

1. `report.md`
2. `manifest.json`
3. `events.jsonl`
4. `metadata.json`
5. `prompts.json`
6. gateway logs

## Session Discovery Commands

```bash
openclaw sessions --limit 20
openclaw sessions --active 120
openclaw sessions --json
```

## Export Command Pattern

```bash
openclaw sessions export-trajectory \
  --session-key "<session-key>" \
  --workspace "." \
  --output "<output-name>" \
  --json
```

## Script Behavior

The helper script should:

- create a timestamped output name
- call `openclaw sessions export-trajectory`
- capture recent gateway logs with `openclaw logs`
- write a compact `report.md`
- print JSON with the output directory and report path
