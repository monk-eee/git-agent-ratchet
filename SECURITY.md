# Security Policy

## Supported versions

`git-agent-ratchet` follows [semantic versioning](https://semver.org/). Only
the latest minor of the most recent major release receives security fixes.

| Version | Supported |
| ------- | --------- |
| 1.x     | yes       |
| < 1.0   | no        |

## Reporting a vulnerability

**Do not open a public issue for security reports.**

If you believe you have found a security issue in `git-agent-ratchet` --
including a way for an LLM coding agent to silently bypass one of the
ratchets in a way the threat model is supposed to catch -- please report it
privately through GitHub's vulnerability reporting flow:

<https://github.com/monk-eee/git-agent-ratchet/security/advisories/new>

Include:

- A description of the issue and the impact.
- Steps to reproduce, ideally with a minimal repro repo or a failing test
  case.
- Your assessment of severity and any suggested mitigations.

We will acknowledge receipt within seven days, give you a status update
within fourteen days, and aim to ship a fix in a patch release as soon as a
correct one is available.

## Threat model

The package is a defence-in-depth layer for the human operator against the
agent the operator is currently driving. It is **not** a sandbox, and it is
**not** a defence against a malicious operator. Specifically in scope:

- An agent that has been given write access to the repository attempts to
  silently weaken a `NON-NEGOTIABLE` rule documented in `AGENTS.md`.
- An agent that mutates the baseline registry, the `.pre-commit-config.yaml`,
  or the ratchet implementations themselves to make a non-compliant commit
  pass.
- An agent that uses `--no-verify`, `git stash` mid-hook, `git add -A` to
  hijack a sibling agent's staged set, or other documented bypasses, in a
  way the ratchets fail to detect.

Out of scope:

- The human operator deliberately disabling the hooks via
  `HUMAN_RATCHET_BYPASS_KEY` in their own shell. That is the documented
  escape hatch.
- Vulnerabilities in `pre-commit`, `uv`, `git`, or the underlying Python
  runtime. Report those upstream.
- Supply-chain attacks against this package's published artefacts. Those
  are mitigated by GitHub Actions provenance + the project's own
  `pre-commit` dogfood pipeline; report directly to GitHub.

## Coordinated disclosure

We follow a 90-day disclosure window from the date the report is
acknowledged. If a fix is not available within 90 days we will agree a
revised timeline with the reporter in writing.
