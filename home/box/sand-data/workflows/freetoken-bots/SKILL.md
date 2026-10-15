---
name: freetoken-bots
description: >-
  Use when finding, verifying, or monitoring zero-priced (free) OpenRouter
  models, e.g. for Pi child-agent fallback, free-model recommendations, or daily
  free-model health checks.
---
# FreeToken-Bots

Source: https://github.com/limin112/min-skill/tree/main/skills/FreeToken-Bots (v0.1.1). The script is a stdlib-only Python file at `/home/box/agent-data/workflows/freetoken-bots/scripts/radar.py`.

Pi is the execution layer. Muse, Grokbot and Dot may invoke it only if they can run shell commands or reach a separately deployed Pi service. Don't claim this replaces those products' native models.

## Principles

- Free means the OpenRouter catalog has `pricing.prompt == 0` and `pricing.completion == 0`, and any explicit request or cache prices are zero too. Free status changes over time; it isn't permanent.
- Classify a model as flagship only when its total parameter count is verified at 100B or more. If the `/models` API omits the count, keep the model in `needs_parameter_verification`, never in the approved pool. Never guess the size from the name.
- Child-agent candidates need `tools` in `supported_parameters`. Probe tool calling separately; a plain completion probe doesn't prove tool support.
- Never route to a paid model automatically. A 402, quota exhaustion or a rate limit is not a reason to remove the user's existing Pi provider configuration.
- `probe --model` resolves the ID against the latest free scan and fails closed. A missing `:free` suffix is auto-corrected with a warning, because the plain ID is the PAID variant; any other unknown ID is refused. A scan older than 24 hours is refreshed first.
- Never put API keys in Git or print key values. Read `OPENROUTER_API_KEY` from the environment, and ask the user for it through a secret input if it's unset.
- Don't rewrite Pi settings without preserving the user's providers and defaults and validating the installed Pi's schema.
- Run every unattended `pi -p` call with `</dev/null`.

## Usage

```bash
cd /home/box/agent-data/workflows/freetoken-bots
python3 scripts/radar.py scan
python3 scripts/radar.py status
python3 scripts/radar.py probe --model 'exact/openrouter-id:free'
python3 scripts/radar.py sync --dry-run
```

- `scan` writes a private report to `~/.pi/agent/freetoken-bots.json`.
- `probe` needs `OPENROUTER_API_KEY` in the environment.
- `sync` only prints a proposal and never modifies `models.json`.

## Pi integration workflow

1. Check `command -v pi`, `pi --version`, `~/.pi/agent/settings.json`, `~/.pi/agent/models.json` and `pi --list-models`, without disclosing keys.
2. Scan. Resolve parameter counts from trustworthy model or provider docs, and move only independently verified 100B+ entries into the approved pool.
3. Probe a plain chat completion, then a separate real `tools` call. Tell a 429 temporary rate limit apart from hard daily-quota exhaustion.
4. Check the OpenRouter model ID, provider compatibility, and the context and max-token fields. Generate a candidate diff, without overwriting custom providers or `enabledModels`.
5. Get the user's explicit approval of the diff before applying it.
   - Back up the original files and write atomically.
   - Run `python3 -m json.tool`, `pi --list-models` and `pi -p 'say pong' --no-extensions </dev/null`.
   - Revert on failure.
6. Grok Bot should call Pi through a controlled shell. First confirm it can run a local Pi command, share the workspace and capture results. Never expose Pi's shell or API to the internet without authentication.
7. Ask the user which model to use before major tasks, and use automatic fallback only after they opt in. Never replay side-effecting actions after an uncertain completion.

## Scheduling

Run `python3 /home/box/agent-data/workflows/freetoken-bots/scripts/radar.py scan` once a day on the machine running Pi, for example from a routine. Compare daily reports for delisted or repriced models, and confirm repeated transient errors before marking a model unusable. Keep `eligible`, `needs_parameter_verification` and inactive as separate states.

## Model selection

Prefer verified free 100B+ tool-capable models. Report a smaller free tool-capable model separately when it's operationally better. If no candidate passes, report an empty pool rather than silently falling back to paid tokens.
