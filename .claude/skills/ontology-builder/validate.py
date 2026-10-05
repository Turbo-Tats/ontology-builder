"""Validate an ontology folder. Fails loudly (exit 1) on any problem.

Usage: python3 .claude/skills/ontology-builder/validate.py docs/ontology/<area> [--removed Name1,Name2]

--removed lists concepts the PM dropped; any mention in the cards or index is reported.
This file is the single source of truth for the allowed status values.
"""
import re
import sys
from pathlib import Path

import yaml

REALIZATION = {"modeled", "fragmented", "conceptual"}
VERSIONING = {"none", "implicit", "explicit"}
EDGE_STATUS = {"current", "target", "confirm"}
NODE_KEYS = {"id", "card", "realization", "versioning", "home", "note"}
EDGE_KEYS = {"from", "rel", "to", "status"}
CARD_KEYS = {"concept", "realization", "versioning", "aliases", "not_to_be_confused_with",
             "system_of_record", "code_names", "identity", "related"}
SECTIONS = ["Definition", "What it is NOT", "Business invariants", "Current realization",
            "Known modeling tensions", "Worked example", "Common agent mistakes"]
LINK = re.compile(r"\]\((?!https?:|#|mailto:)([^)#\s]+)")

errors, warnings = [], []
err = errors.append


def frontmatter(path):
    text = path.read_text()
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not m:
        err(f"{path.name}: no frontmatter block")
        return None, text
    try:
        return yaml.safe_load(m.group(1)), text
    except yaml.YAMLError as e:
        err(f"{path.name}: frontmatter does not parse (quote values containing a colon): {str(e).splitlines()[0]}")
        return None, text


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    folder = Path(args[0]) if args else Path.cwd()
    removed = []
    if "--removed" in sys.argv:
        removed = [r for r in sys.argv[sys.argv.index("--removed") + 1].split(",") if r]

    graph = yaml.safe_load((folder / "graph.yaml").read_text())
    nodes = {n["id"]: n for n in graph.get("nodes", [])}
    if len(nodes) != len(graph.get("nodes", [])):
        err("graph.yaml: duplicate node ids")

    for n in nodes.values():
        missing = NODE_KEYS - n.keys()
        if missing:
            err(f"graph.yaml node {n.get('id')}: missing {sorted(missing)}")
        if n.get("realization") not in REALIZATION:
            err(f"graph.yaml node {n['id']}: realization '{n.get('realization')}' not in {sorted(REALIZATION)}")
        if n.get("versioning") not in VERSIONING:
            err(f"graph.yaml node {n['id']}: versioning '{n.get('versioning')}' not in {sorted(VERSIONING)}")
        if not (folder / n.get("card", "")).is_file():
            err(f"graph.yaml node {n['id']}: card file '{n.get('card')}' does not exist")

    edge_pairs = set()
    for e in graph.get("edges", []):
        missing = EDGE_KEYS - e.keys()
        if missing:
            err(f"graph.yaml edge {e}: missing {sorted(missing)}")
            continue
        for end in ("from", "to"):
            if e[end] not in nodes:
                err(f"graph.yaml edge {e['from']} -> {e['to']}: '{e[end]}' is not a node")
        if e["status"] not in EDGE_STATUS:
            err(f"graph.yaml edge {e['from']} -> {e['to']}: status '{e['status']}' not in {sorted(EDGE_STATUS)}")
        edge_pairs.add(frozenset((e["from"], e["to"])))

    index = folder / "index.md"
    index_text = index.read_text() if index.is_file() else ""
    if not index_text:
        err("index.md is missing")

    if index_text and not re.search(r"^## Using this ontology\s*$", index_text, re.M):
        err("index.md: missing the '## Using this ontology' block that tells agents how to read the cards")

    card_files = {n["card"] for n in nodes.values()}
    stray = [p.name for p in folder.glob("*.md") if p.name != "index.md" and p.name not in card_files]
    for s in stray:
        err(f"{s}: markdown file is not a card for any node in graph.yaml")

    all_text = index_text
    for n in nodes.values():
        card = folder / n["card"]
        if not card.is_file():
            continue
        fm, text = frontmatter(card)
        all_text += text
        if n["card"] not in index_text:
            err(f"index.md does not list {n['card']}")
        for m in LINK.findall(text):
            if m.endswith(".md") and not (card.parent / m).is_file():
                err(f"{card.name}: broken link {m}")
        for sec in SECTIONS:
            if not re.search(rf"^## {re.escape(sec)}\s*$", text, re.M):
                err(f"{card.name}: missing section '## {sec}'")
        inv = re.search(r"## Business invariants(.*?)(?=^## )", text, re.S | re.M)
        if inv:
            for item in re.split(r"\n(?=\s*[-*] )", inv.group(1)):
                if re.match(r"\s*[-*] ", item) and not re.search(r"\[(current|target|confirm)\b", item):
                    err(f"{card.name}: invariant without [current]/[target]/[confirm] tag: {item.strip()[:70]}")
        if not fm:
            continue
        missing = CARD_KEYS - fm.keys()
        if missing:
            err(f"{card.name}: frontmatter missing {sorted(missing)}")
        if fm.get("concept") != n["id"]:
            err(f"{card.name}: concept '{fm.get('concept')}' != graph node id '{n['id']}'")
        for k in ("realization", "versioning"):
            if fm.get(k) != n.get(k):
                err(f"{card.name}: {k} '{fm.get(k)}' != graph.yaml '{n.get(k)}'")
        for r in fm.get("related") or []:
            if r.get("concept") not in nodes:
                err(f"{card.name}: related concept '{r.get('concept')}' is not a node")
            elif frozenset((n["id"], r["concept"])) not in edge_pairs:
                err(f"{card.name}: related {r['concept']} has no edge in graph.yaml")
            if r.get("status") not in EDGE_STATUS:
                err(f"{card.name}: related {r.get('concept')} status '{r.get('status')}' invalid")
        for other in fm.get("not_to_be_confused_with") or []:
            if other not in nodes:
                warnings.append(f"{card.name}: not_to_be_confused_with '{other}' is not a concept in this graph (fine for code-level look-alikes)")

    for name in removed:
        for p in [index] + [folder / n["card"] for n in nodes.values()]:
            if p.is_file() and re.search(rf"\b{re.escape(name)}\b", p.read_text()):
                err(f"{p.name}: mentions removed concept '{name}'")

    confirms = len(re.findall(r"\[confirm\]", all_text))
    print(f"{len(nodes)} nodes, {len(graph.get('edges', []))} edges, {confirms} [confirm] tags still open")
    if errors:
        for w in warnings:
            print(f"warning: {w}")
        print(f"\nFAILED with {len(errors)} problem(s):")
        for e in errors:
            print(f"  - {e}")
        sys.exit(1)
    for w in warnings:
        print(f"warning: {w}")
    print("OK")


main()
