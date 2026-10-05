# ontology-builder

A Claude Code skill that helps a product manager document one area of an app as a business ontology and an interactive knowledge graph, so people, AI agents and tools share one definition per concept.

The ontology describes how the business works, not how the data is stored today. Each concept gets a card with a business layer (definition, what it is not, invariants) and a current-realization layer (where it lives in code and where that falls short). The gaps are an input to data model design.

## What you get

- one concept card per business concept
- `index.md` with a disambiguation table for names that mean several things
- `graph.yaml` with typed relationships between concepts
- `graph.html`, a standalone, dependency-free viewer generated from `graph.yaml`
- a validation script that checks all of it

## Install

Copy this folder into your repo at `.claude/skills/ontology-builder/` (or into `~/.claude/skills/` for all repos). Requires Python 3 and PyYAML (`pip install pyyaml`).

## Use

In Claude Code, ask for it in your own words:

- "Document the checkout area as an ontology"
- "Build a knowledge graph of our billing concepts"
- "Define the concepts for the onboarding flow"

Claude first confirms your goal and scope, proposes a list of concepts from your UI and code, and asks you to correct it. It then investigates the code, shows you what it found, and asks one question at a time. Cards are written into `docs/ontology/<area>/` by default.

You can also run the scripts yourself:

```bash
python3 .claude/skills/ontology-builder/validate.py docs/ontology/<area> [--removed Name1,Name2]
python3 .claude/skills/ontology-builder/build_graph.py docs/ontology/<area>
```

`validate.py` exits with an error if frontmatter does not parse, cards and graph nodes disagree, an edge points at a missing node, a link is broken, the index omits a card, or an invariant has no status tag. It also reports how many `[confirm]` items are still open.

## Conventions worth knowing

- `[current]` means verified in code, `[target]` means the model the business is building toward, `[confirm]` means inferred. Only the product owner can establish a target.
- `realization` (modeled, fragmented, conceptual) and `versioning` (none, implicit, explicit) are separate on purpose.
- The card format is fixed so cards stay consistent. Validation is not configurable.
- Add `title: My ontology graph` at the top of `graph.yaml` to set the viewer's page title.

## Files

- `SKILL.md`: the method and rules Claude follows
- `validate.py`: validation, and the source of truth for allowed status values
- `build_graph.py` and `graph.template.html`: the viewer generator
