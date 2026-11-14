---
type: guide
date: 2026-11-14
lang: en
---

# IVR Flow Linter

Русская инструкция: [README.ru.md](README.ru.md).

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

## Interoperability (experimental)

The adapters are deliberately separate; they do not claim to be a universal IVR connector.

### Asterisk Call Flow Builder graph to IVR Flow

The interop/acfb_to_flow.py adapter converts the observed version 1 graph object into the canonical IVR Flow JSON format. It supports a fail-closed subset of node kinds: start, menu, playback, extension, queue and hangup. Unknown node kinds, duplicate handles, broken references and unsupported versions stop conversion.

The inspected Asterisk Call Flow Builder commit 0ea0693df66217241f5ea62dd512d3a923e6325f builds a normalized graph object internally, but the UI does not expose a JSON download; the current visible export is extensions.conf and JSON serialization remains commented in the inspected source. The example fixture is synthetic and mirrors the observed object shape; it was not exported from a running installation.

Run from the repository root:

    python tools/ivr_flow_linter/interop/acfb_to_flow.py tools/ivr_flow_linter/examples/asterisk-call-flow-builder.graph.synthetic.json --output /tmp/ivr-flow.json
    python tools/ivr_flow_linter/ivr_flow_lint.py /tmp/ivr-flow.json

Important: the inspected exporter follows only the first outgoing edge for extension nodes and chooses one queue target in a fixed handle priority. The adapter preserves declared graph edges and prints warnings when these cases occur. A passing graph lint does not prove that the generated extensions.conf preserves all branches or behaves correctly on Asterisk.

### IVR Flow to an IVR Tester scenario plan

The interop/flow_to_ivr_tester_plan.py adapter builds a path/action planning matrix for the inspected MakingChatbots/ivr-tester Scenario and Step API.

    python tools/ivr_flow_linter/interop/flow_to_ivr_tester_plan.py /tmp/ivr-flow.json --output /tmp/ivr-tester-plan.json

Mapping:
- DTMF digit → press(digit);
- timeout → doNothing();
- invalid input → press the first unused key in 0123456789, when one remains;
- message continuation → doNothing();
- extension/queue outcomes that the inspected Step API cannot assert are recorded as manual routes.

The plan intentionally leaves expected_prompt_transcript null and runtime_ready false. A real IVR Tester whenPrompt must be a function created from the actual prompt transcription; a playback token or audio filename is not a transcript. Real from/to numbers, credentials and transcriber settings must be supplied outside the repository.

### AsteriskLint is a separate downstream check

After a real extensions.conf exists, AsteriskLint can be installed separately and run with:

    asterisklint dialplan-check extensions.conf

It checks Asterisk configuration/dialplan, not the abstract graph. It is GPLv3+ and is not copied or added as a required dependency here.

These adapters and fixtures are synthetic-contract tests only. There is no live Asterisk, PBX, Twilio or audio-call integration test in this change set, and no upstream project has endorsed this interoperability.


### Source metadata and provenance

The adapter preserves flow-level provenance and a per-node interop_source record. Only kind-specific whitelisted fields are copied into metadata (for example extension/ringSeconds or queue_name/strategy/timeout), with canvas coordinates retained separately. Arbitrary metadata is intentionally omitted to avoid accidental transfer of credentials or unrelated private fields. This is not a lossless round-trip format; retain the original graph JSON for reconstruction.
