#!/usr/bin/env python3
"""Convert the observed Asterisk Call Flow Builder graph model to IVR Flow v1."""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parents[1]
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from ivr_flow_lint import lint_flow, render_text  # noqa: E402

SUPPORTED_KINDS = {"start", "menu", "playback", "extension", "queue", "hangup"}
DTMF_KEYS = set("0123456789*#")


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key!r}")
        result[key] = value
    return result


def load_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=_unique_object)
    except OSError as exc:
        raise ValueError(f"cannot read {path}: {exc}") from exc
    except (json.JSONDecodeError, ValueError) as exc:
        raise ValueError(f"invalid JSON in {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError("ACFB graph document must be a JSON object")
    return data


def _fresh_id(base: str, used: set[str]) -> str:
    candidate = base
    suffix = 2
    while candidate in used:
        candidate = f"{base}_{suffix}"
        suffix += 1
    used.add(candidate)
    return candidate


def _node_title(node: dict[str, Any]) -> str:
    data = node.get("data", {})
    if isinstance(data, dict):
        for field in ("title", "label"):
            value = data.get(field)
            if isinstance(value, str) and value.strip():
                return value.strip()
    return str(node.get("id", "unnamed"))


def _event_for_handle(kind: str, handle: Any) -> str:
    if handle is None or handle == "":
        handle = "next"
    if not isinstance(handle, str):
        raise ValueError(f"{kind} node sourceHandle must be a string or null")
    if kind == "menu":
        if handle == "option-invalid":
            return "invalid_input"
        if handle == "option-timeout":
            return "timeout"
        if handle.startswith("option-") and handle[7:]:
            return handle[7:]
        raise ValueError(
            f"unsupported ACFB menu output handle {handle!r}; "
            "expected option-<key>, option-invalid or option-timeout"
        )
    return handle


def convert_graph(graph: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    """Return (canonical_flow, compatibility_warnings)."""
    if graph.get("version") != 1:
        raise ValueError("unsupported ACFB graph version; only version 1 is inspected")
    if not isinstance(graph.get("nodes"), list) or not graph["nodes"]:
        raise ValueError("ACFB graph must contain a non-empty nodes array")
    if not isinstance(graph.get("edges"), list):
        raise ValueError("ACFB graph must contain an edges array")

    raw_nodes: dict[str, dict[str, Any]] = {}
    kinds: dict[str, str] = {}
    used_ids: set[str] = set()

    for index, node in enumerate(graph["nodes"]):
        if not isinstance(node, dict):
            raise ValueError(f"nodes[{index}] must be an object")
        node_id = node.get("id")
        data = node.get("data")
        kind = data.get("kind") if isinstance(data, dict) else None
        if not isinstance(node_id, str) or not node_id.strip():
            raise ValueError(f"nodes[{index}].id must be a non-empty string")
        if node_id in raw_nodes:
            raise ValueError(f"duplicate ACFB node id: {node_id}")
        if not isinstance(kind, str):
            raise ValueError(f"node {node_id!r} has no data.kind")
        if kind not in SUPPORTED_KINDS:
            raise ValueError(
                f"unsupported ACFB node kind {kind!r} on {node_id!r}; "
                f"supported kinds: {', '.join(sorted(SUPPORTED_KINDS))}. "
                "No node is silently discarded."
            )
        raw_nodes[node_id] = node
        kinds[node_id] = kind
        used_ids.add(node_id)

    outgoing: dict[str, list[tuple[str, str]]] = {node_id: [] for node_id in raw_nodes}
    seen_handles: set[tuple[str, str]] = set()
    for index, edge in enumerate(graph["edges"]):
        if not isinstance(edge, dict):
            raise ValueError(f"edges[{index}] must be an object")
        source, target = edge.get("source"), edge.get("target")
        if source not in raw_nodes:
            raise ValueError(f"edges[{index}] references missing source {source!r}")
        if target not in raw_nodes:
            raise ValueError(f"edges[{index}] references missing target {target!r}")
        if kinds[target] == "start":
            raise ValueError("an ACFB edge may not target the start node")
        handle = edge.get("sourceHandle")
        if handle is None or handle == "":
            handle = "next"
        if not isinstance(handle, str):
            raise ValueError(f"edges[{index}].sourceHandle must be a string or null")
        key = (source, handle)
        if key in seen_handles:
            raise ValueError(f"duplicate outgoing handle {handle!r} on node {source!r}")
        seen_handles.add(key)
        outgoing[source].append((handle, target))

    starts = [node_id for node_id, kind in kinds.items() if kind == "start"]
    if len(starts) != 1:
        raise ValueError(f"expected exactly one start node; found {len(starts)}")
    start_id = starts[0]
    start_edges = outgoing[start_id]
    if len(start_edges) != 1 or start_edges[0][0] != "next":
        raise ValueError("start node must have exactly one outgoing 'next' edge")
    entry_target = start_edges[0][1]

    asterisk = graph.get("asterisk", {})
    if not isinstance(asterisk, dict):
        asterisk = {}
    context = asterisk.get("context", "unknown")
    trunk = asterisk.get("trunk", "unknown")
    flow_stub = re.sub(r"[^A-Za-z0-9_.-]+", "-", f"{context}-{trunk}").strip("-") or "flow"
    flow_id = f"acfb-{flow_stub}"

    result_nodes: list[dict[str, Any]] = []
    warnings: list[str] = []

    def add_synthetic_hangup(source_id: str, purpose: str) -> str:
        synthetic_id = _fresh_id(f"__interop_{purpose}_{source_id}", used_ids)
        result_nodes.append({
            "id": synthetic_id,
            "type": "terminal",
            "terminal_kind": "hangup",
            "description": "Synthetic terminal representing the explicit Hangup/end-of-dialplan behavior observed in the ACFB exporter.",
            "transitions": {},
        })
        return synthetic_id

    start_data = raw_nodes[start_id].get("data", {})
    start_meta = start_data.get("meta", {}) if isinstance(start_data, dict) else {}
    start_playback = start_meta.get("playback") if isinstance(start_meta, dict) else None
    if isinstance(start_playback, str) and start_playback.strip():
        prompt_id = _fresh_id(f"__interop_start_prompt_{start_id}", used_ids)
        result_nodes.append({
            "id": prompt_id,
            "type": "message",
            "prompt_asset": start_playback,
            "description": f"ACFB start prompt: {_node_title(raw_nodes[start_id])}",
            "transitions": {"continue": entry_target},
        })
        entrypoints = [prompt_id]
    else:
        entrypoints = [entry_target]

    for node_id, node in raw_nodes.items():
        kind = kinds[node_id]
        if kind == "start":
            continue

        data = node.get("data", {})
        meta = data.get("meta", {}) if isinstance(data, dict) else {}
        if not isinstance(meta, dict):
            meta = {}
        title = _node_title(node)
        edges = outgoing[node_id]

        if kind == "hangup":
            if edges:
                raise ValueError(f"hangup node {node_id!r} must not have outgoing edges")
            result_nodes.append({
                "id": node_id,
                "type": "terminal",
                "terminal_kind": "hangup",
                "description": title,
                "transitions": {},
            })
            continue

        if kind == "menu":
            transitions: dict[str, str] = {}
            for handle, target in edges:
                event = _event_for_handle(kind, handle)
                if event in transitions:
                    raise ValueError(f"duplicate menu event {event!r} on node {node_id!r}")
                if event not in {"timeout", "invalid_input"} and event not in DTMF_KEYS:
                    raise ValueError(
                        f"menu key {event!r} on node {node_id!r} is not a single DTMF key"
                    )
                transitions[event] = target
            result_nodes.append({
                "id": node_id,
                "type": "menu",
                "prompt_asset": meta.get("playback") if isinstance(meta.get("playback"), str) else "",
                "description": title,
                "transitions": transitions,
            })
            continue

        if kind == "playback":
            transitions = {}
            for handle, target in edges:
                event = _event_for_handle(kind, handle)
                if event in transitions:
                    raise ValueError(f"duplicate playback event {event!r} on node {node_id!r}")
                transitions[event] = target
            if not transitions:
                terminal_id = add_synthetic_hangup(node_id, "playback_end")
                transitions["continue"] = terminal_id
            elif len(transitions) > 1:
                warnings.append(
                    f"ACFB_PLAYBACK_EXPORT_FIRST_EDGE_ONLY: node {node_id!r} has "
                    f"{len(transitions)} edges; the inspected exporter follows only exits[0]. "
                    "The canonical graph preserves all declared edges, but extensions.conf may not."
                )
            result_nodes.append({
                "id": node_id,
                "type": "message",
                "prompt_asset": meta.get("sound") if isinstance(meta.get("sound"), str) else "",
                "description": title,
                "transitions": transitions,
            })
            continue

        if kind == "extension":
            transitions = {}
            for handle, target in edges:
                event = _event_for_handle(kind, handle)
                if event in transitions:
                    raise ValueError(f"duplicate extension event {event!r} on node {node_id!r}")
                transitions[event] = target
            if not transitions:
                terminal_id = add_synthetic_hangup(node_id, "extension_end")
                transitions["continue"] = terminal_id
            elif len(transitions) > 1:
                warnings.append(
                    f"ACFB_EXTENSION_EXPORT_FIRST_EDGE_ONLY: node {node_id!r} has "
                    f"{len(transitions)} outcome edges; the inspected exporter uses exits[0] "
                    "without dispatching by sourceHandle. The canonical graph preserves all "
                    "declared edges, but extensions.conf does not."
                )
            result_nodes.append({
                "id": node_id,
                "type": "message",
                "description": f"{title} (ACFB extension step; topology only)",
                "transitions": transitions,
            })
            continue

        if kind == "queue":
            transitions = {}
            for handle, target in edges:
                event = _event_for_handle(kind, handle)
                if event in transitions:
                    raise ValueError(f"duplicate queue event {event!r} on node {node_id!r}")
                transitions[event] = target
            if len(transitions) > 1:
                warnings.append(
                    f"ACFB_QUEUE_EXPORT_COLLAPSES_RESULT_HANDLES: node {node_id!r} has "
                    f"{len(transitions)} queue outcome edges; the inspected exporter selects "
                    "one target in a fixed priority order and does not branch by outcome. "
                    "The canonical graph preserves all declared edges, but extensions.conf does not."
                )
            result_nodes.append({
                "id": node_id,
                "type": "message",
                "description": f"{title} (ACFB queue step; topology only)",
                "transitions": transitions,
            })
            continue

    flow = {
        "schema_version": "1.0",
        "flow_id": flow_id,
        "description": (
            "Converted from the observed Asterisk Call Flow Builder graph model. "
            "This is a static topology representation, not a PBX configuration."
        ),
        "entrypoints": entrypoints,
        "policy": {
            "require_operator_escape": False,
            "require_timeout_fallback": True,
            "require_invalid_input_fallback": True,
        },
        "nodes": result_nodes,
    }
    return flow, warnings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("graph", type=Path, help="JSON in the observed ACFB graph model (version 1)")
    parser.add_argument("-o", "--output", type=Path, help="write canonical IVR Flow JSON here")
    args = parser.parse_args()

    try:
        graph = load_json(args.graph)
        flow, warnings = convert_graph(graph)
    except ValueError as exc:
        print(f"INPUT ERROR: {exc}", file=sys.stderr)
        return 2

    for warning in warnings:
        print(f"WARNING: {warning}", file=sys.stderr)

    lint_result = lint_flow(flow)
    if not lint_result.ok:
        print(render_text(lint_result), file=sys.stderr)
        return 1

    payload = json.dumps(flow, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.write_text(payload, encoding="utf-8")
    else:
        sys.stdout.write(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
