#!/usr/bin/env python3
"""Build a non-executable scenario plan for MakingChatbots/ivr-tester."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parents[1]
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from ivr_flow_lint import lint_flow, load_flow, render_text  # noqa: E402

TARGET_COMMIT = "0685d8707896264106796724b4ff29d821bac7a3"
DTMF_KEYS = "0123456789*#"


def _first_unused_dtmf(used: set[str]) -> str | None:
    return next((key for key in DTMF_KEYS if key not in used), None)


def build_plan(
    flow: dict[str, Any],
    *,
    silence_after_prompt_ms: int = 3000,
    step_timeout_ms: int = 6000,
    max_scenarios: int = 200,
) -> dict[str, Any]:
    if silence_after_prompt_ms < 0 or step_timeout_ms <= 0:
        raise ValueError("silence-after-prompt must be >= 0 and step-timeout must be > 0")
    lint_result = lint_flow(flow)
    if not lint_result.ok:
        raise ValueError("flow has lint errors:\n" + render_text(lint_result))

    nodes = {node["id"]: node for node in flow["nodes"]}
    scenarios: list[dict[str, Any]] = []
    blocked_cycles: list[dict[str, Any]] = []
    manual_routes: list[dict[str, Any]] = []
    truncated = False

    def walk(
        current_id: str,
        entrypoint: str,
        visited: tuple[str, ...],
        path: tuple[str, ...],
        steps: tuple[dict[str, Any], ...],
    ) -> None:
        nonlocal truncated
        if len(scenarios) >= max_scenarios:
            truncated = True
            return
        if current_id in visited:
            blocked_cycles.append({
                "entrypoint": entrypoint,
                "cycle_at": current_id,
                "path_node_ids": list(path + (current_id,)),
                "status": "manual_review_required",
            })
            return

        node = nodes[current_id]
        node_type = node.get("type")
        next_visited = visited + (current_id,)
        next_path = path + (current_id,)

        if node_type == "terminal":
            scenario_number = len(scenarios) + 1
            scenarios.append({
                "name": f"{flow.get('flow_id', 'ivr-flow')}-path-{scenario_number:03d}",
                "entrypoint": entrypoint,
                "path_node_ids": list(next_path),
                "terminal_node_id": current_id,
                "terminal_kind": node.get("terminal_kind", "other"),
                "steps": list(steps),
            })
            return

        transitions = node.get("transitions", {})
        if not isinstance(transitions, dict) or not transitions:
            manual_routes.append({
                "source_node_id": current_id,
                "path_node_ids": list(next_path),
                "reason": "No transition is available to continue the scenario.",
            })
            return

        for event, target in sorted(transitions.items(), key=lambda item: item[0]):
            action: dict[str, Any] | None = None
            mode = "press"

            if node_type == "menu":
                valid_keys = {
                    key for key in transitions
                    if key not in {"timeout", "invalid_input"} and key in DTMF_KEYS
                }
                if event == "timeout":
                    action = {"method": "doNothing"}
                    mode = "wait_for_timeout"
                elif event == "invalid_input":
                    invalid_key = _first_unused_dtmf(valid_keys)
                    if invalid_key is None:
                        manual_routes.append({
                            "source_node_id": current_id,
                            "event": event,
                            "target_node_id": target,
                            "path_node_ids": list(next_path + (target,)),
                            "reason": "All standard DTMF keys are already assigned; choose a platform-supported invalid key manually.",
                        })
                        continue
                    action = {"method": "press", "digits": invalid_key}
                    mode = "invalid_input"
                elif event in DTMF_KEYS:
                    action = {"method": "press", "digits": event}
                else:
                    manual_routes.append({
                        "source_node_id": current_id,
                        "event": event,
                        "target_node_id": target,
                        "path_node_ids": list(next_path + (target,)),
                        "reason": "The event is not a standard DTMF, timeout or invalid-input event.",
                    })
                    continue
            elif node_type == "message" and event == "continue":
                action = {"method": "doNothing"}
                mode = "observe_message"
            else:
                manual_routes.append({
                    "source_node_id": current_id,
                    "event": event,
                    "target_node_id": target,
                    "path_node_ids": list(next_path + (target,)),
                    "reason": "The graph event must be verified manually; it is preserved in the route but is not represented as a synthetic IVR Tester action.",
                })
                if node_type == "message":
                    walk(target, entrypoint, next_visited, next_path, steps)
                continue

            step = {
                "source_node_id": current_id,
                "prompt_asset_reference": node.get("prompt_asset") or None,
                "expected_prompt_transcript": None,
                "requires_actual_prompt_transcript": True,
                "then": action,
                "coverage": mode,
                "silence_after_prompt_ms": silence_after_prompt_ms,
                "timeout_ms": step_timeout_ms,
                "target_node_id": target,
            }
            walk(target, entrypoint, next_visited, next_path, steps + (step,))

    for entrypoint in flow["entrypoints"]:
        walk(entrypoint, entrypoint, (), (), ())

    return {
        "format": "ivr-tester-scenario-plan",
        "format_version": "1.0",
        "source_flow_id": flow.get("flow_id"),
        "target": {
            "repository": "MakingChatbots/ivr-tester",
            "inspected_main_commit": TARGET_COMMIT,
            "api_shape": "Scenario { name, steps } / Step { whenPrompt, then, silenceAfterPrompt, timeout }",
        },
        "runtime_ready": False,
        "runtime_ready_reason": (
            "This is a planning artifact, not executable IVR Tester input. Each "
            "expected_prompt_transcript must be filled from the actual prompt audio; "
            "from/to numbers, Twilio credentials and transcriber configuration are "
            "deliberately not included."
        ),
        "scenario_defaults": {
            "silence_after_prompt_ms": silence_after_prompt_ms,
            "step_timeout_ms": step_timeout_ms,
            "mapping": {
                "DTMF": "then: press(digits)",
                "timeout": "then: doNothing()",
                "message_continue": "then: doNothing()",
                "invalid_input": "press the first unused key in 0123456789*#",
            },
        },
        "scenarios": scenarios,
        "manual_routes": manual_routes,
        "blocked_cycles": blocked_cycles,
        "scenario_limit_reached": truncated,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("flow", type=Path, help="valid canonical IVR Flow JSON")
    parser.add_argument("-o", "--output", type=Path, help="write the plan to this path")
    parser.add_argument("--silence-after-prompt-ms", type=int, default=3000)
    parser.add_argument("--step-timeout-ms", type=int, default=6000)
    parser.add_argument("--max-scenarios", type=int, default=200)
    args = parser.parse_args()

    try:
        flow = load_flow(args.flow)
        result = build_plan(
            flow,
            silence_after_prompt_ms=args.silence_after_prompt_ms,
            step_timeout_ms=args.step_timeout_ms,
            max_scenarios=args.max_scenarios,
        )
    except (OSError, ValueError) as exc:
        print(f"INPUT ERROR: {exc}", file=sys.stderr)
        return 2

    payload = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.write_text(payload, encoding="utf-8")
    else:
        sys.stdout.write(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
