# FreeToken-Bots (safe MVP)

Pi-oriented OpenRouter free-model discovery for Muse, Grokbot and Dot child-agent workflows.

## Commands

```bash
python3 scripts/radar.py scan
python3 scripts/radar.py status
OPENROUTER_API_KEY='your-key' python3 scripts/radar.py probe --model 'exact-model-id'
python3 scripts/radar.py sync --dry-run
```

Uses Python standard library only. `sync` does **not** mutate Pi yet: Pi schema detection, trusted parameter verification, separate tool-call probing and transactional config updates are planned follow-ups. Never install this expecting full unattended failover. The skill documents safe host-side integration steps.

## Box install (2026-10-09)

- Pi `@earendil-works/pi-coding-agent` 1.1.0 (the old `@mariozechner/pi-coding-agent` is deprecated). Pi needs Node >= 22.19, so it runs on a private Node 22.23.3 at `~/.local/opt/node22`; system node stays 20.
  - Package: `~/.local/lib/node_modules/@earendil-works/pi-coding-agent`
  - Command: `/usr/local/bin/pi` (wrapper that execs Node 22)
- Config: `~/.pi/agent/settings.json` (mode 600). No `models.json`; the OpenRouter `:free` models come from Pi's built-in catalog.
  - `defaultProvider` is `openrouter`.
  - `defaultModel` is `nvidia/nemotron-3-ultra-550b-a55b:free`.
  - `enabledModels` holds ultra-550b, super-120b and `thinkingmachines/inkling:free`.
- Key: Pi reads `OPENROUTER_API_KEY` from the environment. It isn't stored in any file, and `auth.json` is empty.
- Non-interactive use: always pass an explicit free ID and `</dev/null`:
  `pi --model openrouter/nvidia/nemotron-3-ultra-550b-a55b:free -p 'task' --no-extensions --no-session </dev/null`
  - An explicit `--model` is matched strictly. A `:free` ID never resolves to its paid twin; a missing ID errors or is sent as-is.
  - Without `--model`, if a `:free` ID ever disappears from the catalog, Pi falls back to a built-in default, which may be PAID (openrouter: `moonshotai/kimi-k2.6`).
- `inkling:free` returns 403 "only available on agentic harnesses" over the raw API, but works through Pi.
