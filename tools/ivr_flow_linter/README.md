# IVR Flow Linter

A small, dependency-free Python tool that checks a **declared IVR call-flow graph** before a flow is handed to a telephony integrator or implemented in a PBX.

It looks for:
- missing entrypoints and transition targets;
- duplicate node IDs and duplicate JSON keys;
- menu nodes without policy-required timeout / invalid-input fallbacks;
- nodes that callers cannot reach from an entrypoint;
- reachable nodes with no path to any terminal outcome;
- missing operator escape paths when the flow policy requires one;
- cycles that need an explicit repetition / back-navigation review.

It does **not** connect to a PBX, parse vendor-specific routing exports, verify that a key is actually configured, inspect or listen to audio files, test a telephone line, or guarantee accessibility/usability. A static PASS means only that the declared graph passed these checks.

## Requirements

- Python 3.10 or newer
- No third-party dependencies

## Run

```bash
python tools/ivr_flow_linter/ivr_flow_lint.py tools/ivr_flow_linter/examples/valid-flow.json
```

Machine-readable output:

```bash
python tools/ivr_flow_linter/ivr_flow_lint.py tools/ivr_flow_linter/examples/valid-flow.json --json
```

Exit codes: `0` = no errors (warnings may remain); `1` = graph errors; `2` = input / JSON error.

## Input model

See `schema/ivr-flow.schema.json` and `examples/valid-flow.json`.

- `entrypoints` lists the IDs where callers can enter the declared flow.
- `nodes` is the set of menus, messages and terminal outcomes.
- `transitions` maps an event (`1`, `2`, `timeout`, `invalid_input`, `continue`, etc.) to another node ID.
- `policy` states which project-specific guardrails are required. Operator escape is not forced universally; enable it when the intended flow must offer a human route.
- `terminal_kind` describes a terminal outcome such as operator, queue or hangup.

The linter intentionally does not impose a universal telephone audio format or a universal menu depth. Those depend on the specific PBX, integrator specification and caller task.

## Test

```bash
python -m unittest discover -s tools/ivr_flow_linter/tests -v
```

## Examples

- `examples/valid-flow.json` is a fictional support menu that passes.
- `examples/invalid-flow.json` is a fictional negative fixture with an undefined target, a closed loop and an unreachable node.

Neither example is a client case, a recommended production flow, or evidence about a live telephony system.

## Method and license

The checks operationalize a subset of the repository's IVR design/release standard: explicit timeout and invalid-input behavior, no caller dead ends, and a human route when the project policy requires it. The standard separately requires live/test-number verification and listening through a telephone path.

Repository material is distributed under the terms in the root `LICENSE` (CC BY 4.0). Attribution is required; users must review the license and any third-party constraints before reuse.