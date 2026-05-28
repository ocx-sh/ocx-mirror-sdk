# Setup

This repo dogfoods OCX. Install OCX once, then everything runs through
`ocx run`.

```bash
curl -sSL https://setup.ocx.sh | sh
git clone https://github.com/ocx-sh/ocx-mirror-sdk
cd ocx-mirror-sdk
ocx run -- task verify
```

OCX bootstraps:

- `task` (Taskfile v3) — task runner
- `uv` — Python package manager + script runner

`uv` provisions Python 3.13+ and installs the optional `dev` and
`docs` dependency groups on demand.

## Optional: drop the `ocx run --` prefix

```bash
eval "$(ocx env --shell=sh)"   # add to your shell profile if you like
task verify
task docs:serve
```
