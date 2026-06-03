# TODO

Progress tracker, known gaps, and triage list.

## Shipped

- [x] docs/spec.md v1.0.0 -- the contract
- [x] Package scaffold (`git_agent_ratchet/`, flat layout, hatchling)
- [x] Baseline registry (`Baseline` dataclass + JSON I/O)
- [x] Ratchet A (duplicate helpers, AST scan)
- [x] Ratchet B (agent chatter, regex scan)
- [x] Ratchet C (anti-bypass, env + protected-files guard)
- [x] Three hook entry points + unified CLI dispatcher
- [x] `.pre-commit-hooks.yaml` manifest for downstream consumers
- [x] `.pre-commit-config.yaml` (this repo dogfoods its own ratchets)
- [x] README.md (long-form, with HUMANS.md framing)
- [x] AGENTS.md (mechanical enforcement table)
- [x] DEVELOPERS.md (human contributor view)
- [x] Test suite covering baseline, ratchets, hooks, CLI
- [x] Makefile (`setup`, `test`, `lint`, `format`, `ratchet`, `seed-baseline`)
- [x] GitHub Actions CI (test matrix + lint + pre-commit + build)
- [x] LICENSE (MIT)

## Next

- [ ] Tag v1.0.0 once CI is green end-to-end
- [ ] PyPI publish workflow (trusted publisher)
- [ ] Example downstream consumer repo to validate the published manifest
- [ ] Add a `--max-file-lines` ratchet to enforce the 350-line soft rule
- [ ] Pluggable language support for Ratchet A (currently Python-only)

## Known soft rules

See [DEVELOPERS.md](DEVELOPERS.md) for the table. Each entry there is a
candidate ratchet.

## Known bugs

_None reported. When you spot one while doing other work, log it here with:
(1) what you observed, (2) where (file + symbol or test name),
(3) impact / blast radius, (4) whether you fixed it in this run or left
it for later._

## Known duplicates

_Empty. Ratchet A enforces this mechanically; any duplicate that survives
a commit lives here with a note explaining why the cleanup hasn't landed
yet._
