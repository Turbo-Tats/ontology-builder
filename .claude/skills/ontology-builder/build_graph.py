"""Build graph.html from graph.yaml so the viewer stays in sync with the ontology.

Usage: python3 .claude/skills/ontology-builder/build_graph.py docs/ontology/<area>
Requires PyYAML. Writes graph.html into the given folder.
The page title comes from an optional top-level `title:` in graph.yaml.
"""
import html
import json
import sys
from pathlib import Path

import yaml

template_path = Path(__file__).parent / "graph.template.html"
folder = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd()
graph = yaml.safe_load((folder / "graph.yaml").read_text())
out = folder / "graph.html"
title = html.escape(str(graph.get("title", "Ontology graph")))
page = template_path.read_text().replace("/*TITLE*/", title).replace("/*GRAPH_JSON*/", json.dumps(graph))
out.write_text(page)
print(f"wrote {out}: {len(graph['nodes'])} nodes, {len(graph['edges'])} edges")
