#!/usr/bin/env python3
"""Static linter for declared IVR call-flow graphs.

This tool validates the declared graph only. It does not connect to a PBX,
verify live routing, inspect audio assets, or prove that a caller can complete
a real telephone interaction.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict, deque
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable

ALLOWED_NODE_TYPES = {"menu", "message", "terminal"}
ALLOWED_TERMINAL_KINDS = {
    "operator", "queue", "voicemail", "hangup", "external_transfer", "other"
}
DEFAULT_POLICY = {
    "require_operator_escape": False,
    "require_timeout_fallback": True,
    "require_invalid_input_fallback": True,
}


@dataclass(frozen=True)
class Finding:
    severity: str
    code: str
    location: str
    message: str


@dataclass
class LintResult:
    flow_id: str | None
    findings: list[Finding]

    @property
    def errors(self) -> list[Finding]:
        return [f for f in self.findings if f.severity == "ERROR"]

    @property
    def warnings(self) -> list[Finding]:
        return [f for f in self.findings if f.severity == "WARNING"]

    @property
    def ok(self) -> bool:
        return not self.errors

    def to_dict(self) -> dict[str, Any]:
        return {
            "flow_id": self.flow_id,
            "ok": self.ok,
            "error_count": len(self.errors),
            "warning_count": len(self.warnings),
            "findings": [asdict(f) for f in self.findings],
        }


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    """Reject duplicate JSON object keys instead of silently keeping the last."""
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key!r}")
        result[key] = value
    return result


def load_flow(path: Path) -> dict[str, Any]:
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise OSError(f"cannot read {path}: {exc}") from exc
    try:
        data = json.loads(raw, object_pairs_hook=_unique_object)
    except (json.JSONDecodeError, ValueError) as exc:
        raise ValueError(f"invalid JSON in {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError("flow document must be a JSON object")
    return data


def _as_string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, str) and item]


def _reachable(starts: Iterable[str], adjacency: dict[str, set[str]]) -> set[str]:
    seen: set[str] = set()
    queue = deque(starts)
    while queue:
        current = queue.popleft()
        if current in seen:
            continue
        seen.add(current)
        queue.extend(adjacency.get(current, set()) - seen)
    return seen


def _nodes_that_can_reach(targets: set[str], adjacency: dict[str, set[str]]) -> set[str]:
    reverse: dict[str, set[str]] = defaultdict(set)
    for source, destinations in adjacency.items():
        for destination in destinations:
            reverse[destination].add(source)
    return _reachable(targets, reverse)


def _cycle_nodes(nodes: set[str], adjacency: dict[str, set[str]]) -> set[str]:
    """Return nodes that participate in a directed cycle (Tarjan SCC)."""
    index = 0
    stack: list[str] = []
    on_stack: set[str] = set()
    indices: dict[str, int] = {}
    lowlink: dict[str, int] = {}
    cycle_nodes: set[str] = set()

    def visit(node: str) -> None:
        nonlocal index
        indices[node] = lowlink[node] = index
        index += 1
        stack.append(node)
        on_stack.add(node)
        for nxt in adjacency.get(node, set()):
            if nxt not in nodes:
                continue
            if nxt not in indices:
                visit(nxt)
                lowlink[node] = min(lowlink[node], lowlink[nxt])
            elif nxt in on_stack:
                lowlink[node] = min(lowlink[node], indices[nxt])
        if lowlink[node] == indices[node]:
            component: list[str] = []
            while True:
                member = stack.pop()
                on_stack.remove(member)
                component.append(member)
                if member == node:
                    break
            if len(component) > 1 or node in adjacency.get(node, set()):
                cycle_nodes.update(component)

    for node in nodes:
        if node not in indices:
            visit(node)
    return cycle_nodes


def lint_flow(data: dict[str, Any]) -> LintResult:
    findings: list[Finding] = []
    flow_id = data.get("flow_id") if isinstance(data.get("flow_id"), str) else None

    def add(severity: str, code: str, location: str, message: str) -> None:
        findings.append(Finding(severity, code, location, message))

    if data.get("schema_version") != "1.0":
        add("ERROR", "SCHEMA_VERSION", "schema_version", "schema_version must be '1.0'.")
    if not flow_id or not flow_id.strip():
        add("ERROR", "FLOW_ID", "flow_id", "flow_id must be a non-empty string.")

    raw_entrypoints = data.get("entrypoints")
    if isinstance(raw_entrypoints, list) and any(not isinstance(item, str) or not item.strip() for item in raw_entrypoints):
        add("ERROR", "ENTRYPOINT_VALUE", "entrypoints", "Every entrypoint must be a non-empty string.")
    entrypoints = _as_string_list(raw_entrypoints)
    if not entrypoints:
        add("ERROR", "NO_ENTRYPOINT", "entrypoints", "Declare at least one entrypoint node id.")

    raw_policy = data.get("policy", {})
    if not isinstance(raw_policy, dict):
        add("ERROR", "POLICY_TYPE", "policy", "policy must be a JSON object.")
        raw_policy = {}
    policy = dict(DEFAULT_POLICY)
    for key in DEFAULT_POLICY:
        if key in raw_policy:
            if not isinstance(raw_policy[key], bool):
                add("ERROR", "POLICY_VALUE", f"policy.{key}", "Policy values must be true or false.")
            else:
                policy[key] = raw_policy[key]

    raw_nodes = data.get("nodes")
    if not isinstance(raw_nodes, list):
        add("ERROR", "NODES_TYPE", "nodes", "nodes must be an array of node objects.")
        raw_nodes = []

    nodes: dict[str, dict[str, Any]] = {}
    for index, node in enumerate(raw_nodes):
        loc = f"nodes[{index}]"
        if not isinstance(node, dict):
            add("ERROR", "NODE_TYPE", loc, "Each node must be an object.")
            continue
        node_id = node.get("id")
        if not isinstance(node_id, str) or not node_id.strip():
            add("ERROR", "NODE_ID", f"{loc}.id", "Node id must be a non-empty string.")
            continue
        node_id = node_id.strip()
        if node_id in nodes:
            add("ERROR", "DUPLICATE_NODE_ID", f"{loc}.id", f"Node id {node_id!r} is declared more than once.")
            continue
        nodes[node_id] = node
        node_type = node.get("type")
        if node_type not in ALLOWED_NODE_TYPES:
            add("ERROR", "NODE_TYPE_VALUE", f"nodes[{node_id}].type", f"type must be one of {sorted(ALLOWED_NODE_TYPES)}.")
        transitions = node.get("transitions", {})
        if not isinstance(transitions, dict):
            add("ERROR", "TRANSITIONS_TYPE", f"nodes[{node_id}].transitions", "transitions must be an object mapping events to node ids.")
        if node_type == "terminal":
            terminal_kind = node.get("terminal_kind")
            if terminal_kind not in ALLOWED_TERMINAL_KINDS:
                add("ERROR", "TERMINAL_KIND", f"nodes[{node_id}].terminal_kind", f"terminal_kind must be one of {sorted(ALLOWED_TERMINAL_KINDS)}.")
            if isinstance(transitions, dict) and transitions:
                add("ERROR", "TERMINAL_HAS_TRANSITIONS", f"nodes[{node_id}].transitions", "Terminal nodes must not have outgoing transitions; model the next action as a separate node if it belongs in this flow.")
        if node_type == "menu":
            if policy["require_timeout_fallback"] and "timeout" not in transitions:
                add("ERROR", "MISSING_TIMEOUT", f"nodes[{node_id}].transitions", "Menu is missing an explicit timeout fallback required by policy.")
            if policy["require_invalid_input_fallback"] and "invalid_input" not in transitions:
                add("ERROR", "MISSING_INVALID_INPUT", f"nodes[{node_id}].transitions", "Menu is missing an explicit invalid_input fallback required by policy.")

    adjacency: dict[str, set[str]] = {node_id: set() for node_id in nodes}
    for node_id, node in nodes.items():
        transitions = node.get("transitions", {})
        if not isinstance(transitions, dict):
            continue
        for event, target in transitions.items():
            loc = f"nodes[{node_id}].transitions.{event}"
            if not isinstance(event, str) or not event.strip():
                add("ERROR", "TRANSITION_EVENT", loc, "Transition event names must be non-empty strings.")
                continue
            if not isinstance(target, str) or not target.strip():
                add("ERROR", "TRANSITION_TARGET_TYPE", loc, "Transition target must be a non-empty node id string.")
                continue
            target = target.strip()
            if target not in nodes:
                add("ERROR", "MISSING_TARGET", loc, f"Transition points to undefined node {target!r}.")
                continue
            adjacency[node_id].add(target)

    for entrypoint in entrypoints:
        if entrypoint not in nodes:
            add("ERROR", "MISSING_ENTRYPOINT", "entrypoints", f"Entrypoint {entrypoint!r} is not defined in nodes.")

    valid_entrypoints = [e for e in entrypoints if e in nodes]
    reachable = _reachable(valid_entrypoints, adjacency)
    for node_id in sorted(set(nodes) - reachable):
        add("WARNING", "UNREACHABLE_NODE", f"nodes[{node_id}]", "Node is not reachable from any declared entrypoint.")

    reachable_terminals = {
        node_id for node_id in reachable
        if nodes[node_id].get("type") == "terminal"
    }
    can_reach_terminal = _nodes_that_can_reach(reachable_terminals, adjacency)
    for node_id in sorted(reachable - can_reach_terminal):
        add("ERROR", "NO_TERMINAL_PATH", f"nodes[{node_id}]", "Reachable node cannot reach any terminal outcome; callers may be trapped in a dead end or closed loop.")

    if policy["require_operator_escape"]:
        operator_nodes = {
            node_id for node_id in reachable
            if nodes[node_id].get("type") == "terminal"
            and nodes[node_id].get("terminal_kind") == "operator"
        }
        can_reach_operator = _nodes_that_can_reach(operator_nodes, adjacency)
        for node_id in sorted(reachable - can_reach_operator):
            if nodes[node_id].get("type") != "terminal":
                add("ERROR", "NO_OPERATOR_ESCAPE", f"nodes[{node_id}]", "Policy requires an operator path, but this node cannot reach an operator terminal.")

    cycle_nodes = _cycle_nodes(reachable, adjacency)
    if cycle_nodes:
        add("WARNING", "CYCLE_PRESENT", "nodes", "Reachable cycle detected among: " + ", ".join(sorted(cycle_nodes)) + ". Confirm that repetition limits, back-navigation and escape behavior are explicitly tested on the real telephone platform.")

    return LintResult(flow_id=flow_id, findings=findings)


def render_text(result: LintResult) -> str:
    label = "PASS" if result.ok else "FAIL"
    lines = [f"{label}: flow={result.flow_id or '(unnamed)'} errors={len(result.errors)} warnings={len(result.warnings)}"]
    for finding in result.findings:
        lines.append(f"{finding.severity} [{finding.code}] {finding.location}: {finding.message}")
    if not result.findings:
        lines.append("No structural issues found in the declared flow graph.")
    lines.append("Scope: static graph checks only; no live PBX, route, or audio-file test was performed.")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Lint a declared IVR menu flow (static JSON graph checks).")
    parser.add_argument("flow", type=Path, help="Path to an IVR flow JSON file")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON findings")
    args = parser.parse_args(argv)

    try:
        data = load_flow(args.flow)
    except (OSError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    result = lint_flow(data)
    if args.json:
        print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
    else:
        print(render_text(result))
    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
