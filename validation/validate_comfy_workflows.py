#!/usr/bin/env python3
"""Offline structure-only validator for nested ComfyUI UI graphs and API prompts.

No ComfyUI imports, model downloads, inference or filesystem writes unless
--report is explicitly supplied. This validates links, not node signatures,
runtime compatibility, licensing or actual media content.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
import sys


SKIP_NAMES = {"SOURCE_LOCK.json", "orbit_turn.json", "fit_requirements.json", "WORKFLOW_MANIFEST.json"}


def graphs(value):
    """Locate nested UI graphs, without recursing through unbounded JSON."""
    pending = [("$", value, 0)]
    count = 0
    while pending:
        path, item, depth = pending.pop()
        count += 1
        if count > 250000 or depth > 256:
            raise ValueError("workflow nesting or node budget exceeded")
        if isinstance(item, dict):
            if isinstance(item.get("nodes"), list) and isinstance(item.get("links"), list):
                yield path, item
            for key, sub in reversed(list(item.items())):
                if isinstance(sub, (dict, list)):
                    pending.append((f"{path}.{key}", sub, depth + 1))
        elif isinstance(item, list):
            for idx in range(len(item) - 1, -1, -1):
                sub = item[idx]
                if isinstance(sub, (dict, list)):
                    pending.append((f"{path}[{idx}]", sub, depth + 1))


def _is_int(value):
    return type(value) is int


def _link_id(value):
    if isinstance(value, list) and value:
        return value[0] if _is_int(value[0]) else None
    if isinstance(value, dict):
        index = value.get("id")
        return index if _is_int(index) else None
    return None


def _ui(g, path, errors, warnings):
    nodes = g["nodes"]
    links = g["links"]
    indexed = {}
    for pos, node in enumerate(nodes):
        if not isinstance(node, dict):
            errors.append(f"{path}: node {pos} is not an object")
            continue
        ident = node.get("id")
        if not _is_int(ident):
            errors.append(f"{path}: node {pos} has invalid id")
            continue
        if ident in indexed:
            errors.append(f"{path}: duplicate node id")
        indexed[ident] = node
        if not isinstance(node.get("type"), str) or not node["type"]:
            errors.append(f"{path}: node {pos} has invalid type")
        for field in ("inputs", "outputs"):
            if field in node and not isinstance(node[field], list):
                errors.append(f"{path}: node {pos} {field} must be an array")
    seen_links = set()
    for link in links:
        lid = _link_id(link)
        if lid is None:
            errors.append(f"{path}: invalid link id")
            continue
        if lid in seen_links:
            errors.append(f"{path}: duplicate link ID")
        seen_links.add(lid)
        if not isinstance(link, list) or len(link) < 6:
            # Historical nested upstream graphs sometimes use object-based
            # link serialization. Its semantics cannot be checked here.
            warnings.append(f"{path}: nonstandard link object")
            continue
        _, oid, oslot, tid, tslot, _ = link[:6]
        for node_id, slot, ports_field, side in (
            (oid, oslot, "outputs", "origin"), (tid, tslot, "inputs", "target")
        ):
            if not _is_int(node_id) or node_id not in indexed:
                errors.append(f"{path}: link {lid} references missing {side} node")
                continue
            node_ports = indexed[node_id].get(ports_field, [])
            if not isinstance(node_ports, list) or not _is_int(slot) or not 0 <= slot < len(node_ports):
                errors.append(f"{path}: link {lid} invalid {side} slot")
    for node in nodes:
        if not isinstance(node, dict) or not _is_int(node.get("id")):
            continue
        inputs = node.get("inputs", [])
        if not isinstance(inputs, list):
            continue
        for port in inputs:
            if not isinstance(port, dict):
                errors.append(f"{path}: non-object node input")
                continue
            lid = port.get("link")
            if lid is not None and (not _is_int(lid) or lid not in seen_links):
                errors.append(f"{path}: input references invalid or missing link")


def _is_api(value):
    return (
        isinstance(value, dict)
        and bool(value)
        and all(isinstance(node, dict) and "class_type" in node for node in value.values())
    )


def _api(value, errors):
    for node_id, node in value.items():
        if not isinstance(node_id, str) or not re.fullmatch(r"[0-9]+(?::[0-9]+)*", node_id):
            errors.append("API node has invalid numeric-string id")
        if not isinstance(node.get("class_type"), str) or not node["class_type"]:
            errors.append("API node has invalid class_type")
        inputs = node.get("inputs", {})
        if not isinstance(inputs, dict):
            errors.append(f"API node {node_id} inputs must be an object")
            continue
        for name, data in inputs.items():
            if (isinstance(data, list) and len(data) == 2
                    and isinstance(data[0], str) and _is_int(data[1]) or
                    isinstance(data, list) and len(data) == 2
                    and isinstance(data[0], str) and type(data[1]) is bool):
                upstream, slot = data
                if not _is_int(slot) or slot < 0:
                    errors.append(f"API node {node_id} input {name} invalid upstream slot")
                elif upstream not in value:
                    errors.append(f"API node {node_id} input {name} missing upstream node")


def validate(path):
    errors = []
    warnings = []
    count = 0
    kind = "unknown"
    try:
        with Path(path).open(encoding="utf-8") as stream:
            doc = json.load(stream)
        found = list(graphs(doc))
        for gp, graph in found:
            _ui(graph, gp, errors, warnings)
        if found:
            count = len(found)
            kind = "ui"
        elif _is_api(doc):
            count = 1
            kind = "api"
            _api(doc, errors)
        else:
            errors.append("no recognised ComfyUI UI or API graph")
        serialized = json.dumps(doc, ensure_ascii=False)
        for forbidden in ("GunCatch", "fight_test", "FightTest"):
            if forbidden.lower() in serialized.lower():
                errors.append(f"forbidden leftover string: {forbidden}")
        if "orbit_and_turn_4K8Bit_01.mov" not in serialized:
            warnings.append("Orbit source filename not found")
    except (OSError, UnicodeError, ValueError, RecursionError, TypeError):
        errors.append("unreadable or excessively nested JSON workflow")
    return {
        "file": str(path), "graphs": count, "format": kind,
        "errors": errors, "warnings": warnings, "ok": not errors
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="+")
    parser.add_argument("--report")
    args = parser.parse_args(argv)
    files = []
    for name in args.paths:
        path = Path(name)
        if path.is_dir() and not path.is_symlink():
            files.extend(sorted(path.rglob("*.json")))
        else:
            files.append(path)
    files = list(dict.fromkeys(p for p in files if p.name not in SKIP_NAMES))
    if not files:
        print(json.dumps({"ok": False, "errors": ["no workflow JSON files"]}))
        return 1
    output = [validate(path) for path in files]
    text = json.dumps(output, indent=2)
    print(text)
    if args.report:
        report = Path(args.report)
        with report.open("x", encoding="utf-8") as writer:
            writer.write(text + "\n")
    return int(any(not x["ok"] for x in output))


if __name__ == "__main__":
    sys.exit(main())
