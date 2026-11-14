---
type: guide
date: 2026-11-14
lang: en
---

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

See `schema/ivr-flow.schema.json` and `examples/valid-flow.json`. The JSON Schema documents the input contract; the CLI performs its own static checks with the Python standard library and does not invoke an external JSON Schema validator.

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

## Related tools and boundaries

This utility is a preflight check for a vendor-neutral JSON graph. It is not a replacement for adjacent IVR tools:

- [Asterisk Call Flow Builder](https://github.com/michaelnabil230/asterisk-call-flow-builder) describes itself as a visual editor for Asterisk inbound flows that validates a graph and exports an Asterisk dialplan. Use a visual editor when designing and exporting an Asterisk-specific flow; this linter checks a separate declarative JSON contract in a local script or CI.
- [MakingChatbots/ivr-tester](https://github.com/MakingChatbots/ivr-tester) is an automated IVR testing framework that calls a real number and exercises prompts / DTMF interactions. That is a runtime test; this linter does not place calls.
- [ossobv/asterisklint](https://github.com/ossobv/asterisklint) checks Asterisk PBX configuration and dialplan syntax. This linter does not parse Asterisk configuration; it checks the abstract graph before a vendor-specific dialplan exists.

The tools can be complementary in a pipeline: declare the intended flow → lint its graph → generate or configure the PBX flow → run tests against a test number → verify the final audio through the telephone path.

## Method and license

The checks operationalize a subset of the repository's IVR design/release standard: explicit timeout and invalid-input behavior, no caller dead ends, and a human route when the project policy requires it. The standard separately requires live/test-number verification and listening through a telephone path.

Repository material is distributed under the terms in the root `LICENSE` (CC BY 4.0). Attribution is required; users must review the license and any third-party constraints before reuse.