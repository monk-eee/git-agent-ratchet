# Example downstream consumer

A minimal repository layout that wires `git-agent-ratchet` into a
downstream project via pre-commit. Two purposes:

1. **Copy-paste template** -- the shape of files you want in a real repo
   that adopts the ratchets.
2. **Manifest validation harness** -- a way to verify that the published
   `.pre-commit-hooks.yaml` actually resolves and executes against a
   clean tree.

## Layout

```
examples/downstream/
|-- .pre-commit-config.yaml         # production-shape config
|-- src/
|   `-- example.py                  # clean Python so the seed run passes
`-- config/ratchets/
    |-- duplicates.json             # empty baseline for Ratchet A
    `-- file_lines.json             # empty baseline for Ratchet D
```

## Using as a template

Copy the four files into your repository root, then edit
`.pre-commit-config.yaml`:

- Change `--dir=src` to point at the package directory you want scanned.
- Adjust `--enforce-files=...` on `ratchet-anti-bypass` to list any
  additional config files you want pinned.
- Pin `rev:` to a released tag of `git-agent-ratchet` (do not float).

Then install:

```bash
pre-commit install
pre-commit run --all-files
```

The first run seeds the baselines under `config/ratchets/`. Commit the
seeded files. From then on every commit ratchets the metrics down or
holds them flat.

## Validating the published manifest locally

From the repository root (the parent of this directory):

```bash
pre-commit try-repo . ratchet-no-duplicate-helpers \
    --files examples/downstream/src/example.py
pre-commit try-repo . ratchet-deny-agent-chatter \
    --files examples/downstream/src/example.py
pre-commit try-repo . ratchet-anti-bypass \
    --files examples/downstream/src/example.py
pre-commit try-repo . ratchet-max-file-lines \
    --files examples/downstream/src/example.py
```

`try-repo .` resolves the hook ids out of `.pre-commit-hooks.yaml`,
installs the package into an isolated venv from the working tree, and
runs each entry point. If the published manifest is structurally broken,
this is where it shows up.

## Why this lives inside the main repo

A separate repository for an example would drift. Keeping the harness
inside `git-agent-ratchet/examples/downstream/` means each change to the
manifest, CLI surface, or hook arguments is tested against a realistic
config in the same commit.
