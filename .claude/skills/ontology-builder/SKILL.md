---
name: ontology-builder
description: Document an area of the app as a business ontology plus an interactive knowledge graph, so people, agents and an MCP server share one definition per concept. Use when the user says "document this area as an ontology", "build a knowledge graph of X", "define the concepts for Y", or "write agent documentation for Z".
---

# Ontology builder

Produces, for one app area, concept cards, an index, a typed-relationship `graph.yaml`, and an interactive `graph.html`, then validates them. The card skeleton and graph format below are the format to follow. If the repo already has an ontology, read an existing card or two for tone and depth before drafting.

Audience default: a product manager. Use plain language and short replies, and keep code names inside the cards. Ask one plain-text question at a time, never multiple choice, because multiple choice forces a pick between possibly faulty options. Follow the repo's own conventions for branching (one branch per unit of work, never commit to the main branch), PR size (propose a split up front if the area is large; under about 1,000 inserted lines reviews well) and PR descriptions.

## Core stance

The ontology describes **how the business works, not how the data is stored today.** Code is evidence of current fragmentation, not the source of definitions. Each card has a business layer (definition, boundaries, invariants) and a current-realization layer (tables, columns, gaps). The gaps are an input to data model design.

## Phase 0: frame the work (guided)

Start with one short paragraph, in plain language, on what the PM will get: a card per business concept, a graph of how they relate, and an interactive viewer, all checked by a script. Then walk through these steps. One plain-text question at a time, each with your recommendation so the PM can accept, correct or reject it. Skip any step the PM's opening request already answers.

1. **Goal.** If the request states the goal, confirm it back in one line and move on. If not, ask what the documentation is for (for example: help agents avoid mistakes, align the team on terms, feed data model design) and recommend one. The goal sets the emphasis: agent-oriented work leans on "What it is NOT" and "Common agent mistakes"; design-oriented work leans on tensions and design questions.
2. **Scope.** Recommend a boundary (one flow, one set of tables or screens) and what is out. If the area looks too big for one PR, say so now and propose a split.
3. **Sources.** Ask for diagrams, specs or handoff notes (Figma boards load in the built-in browser; zoom to read small text). If there are none, say you will start from the UI and code. State which sources are proposals rather than facts. Also confirm the owner and the output folder (default `docs/ontology/<area>/`).
4. **Concept list: you propose first.** Scan the area's UI labels, routes, tables and docs, then propose candidate concepts with a one-line definition each. Flag suspected name collisions (one word used for several things) and concepts that look missing. Recommend merges and splits. The PM adds, removes and renames.
5. **Confirm the brief.** Show goal, scope, concept list, folder and expected PR split in a few lines. Proceed to the method only after the PM approves.

Check in again after the first two cards are drafted, so the PM confirms the pattern before you batch the rest.

## Files produced

```
index.md            concept table, status definitions, disambiguation table, cross-cutting rules, sources
<concept-slug>.md   one card per concept (kebab-case file, PascalCase concept id)
graph.yaml          nodes and typed edges
graph.html          generated, committed
_references/        proposals and source docs, linked, never merged into cards
```

Do not copy `graph.template.html` or `build_graph.py` into the area. Run them from this skill's folder.

## Method

1. **Orient** (after Phase 0). Read the area's docs (architecture or onboarding docs, contributor guides, feature docs, if the repo has them). Note which statements are proposals, not facts. Treat repo docs as evidence, not truth; they go stale. Record contradictions as findings.
2. **Concept list changes are normal.** Phase 0 agrees the first list; expect the PM to add, remove and rename as findings arrive. Re-confirm the brief when it changes materially.
3. **Investigate before asking.** For each cluster of concepts, launch read-only investigation agents in parallel (see brief below). Cross-check load-bearing claims yourself; agents are fallible.
4. **Present findings, then ask one question** only the PM can answer. Show what the code says and where it contradicts the PM.
5. **Capture corrections immediately**, in the same turn, in the cards. Update the graph and index when a card changes.
6. **Draft one concept at a time**, show it, refine. After the first few, batch the rest.
7. **Consistency read** before calling a batch done (below).
8. **Validate, build, offer to commit.**

```bash
python3 .claude/skills/ontology-builder/validate.py docs/ontology/<area> [--removed Name1,Name2]
python3 .claude/skills/ontology-builder/build_graph.py docs/ontology/<area>
```

Do not pipe either to `head` or `tail`; some shells hang. Redirect to a file instead.

### Investigation agent brief (template)

> Read-only. For the concepts [list] in [repo paths], report: exact tables, columns, enums, lifecycle states, creation paths, identity keys, naming collisions (UI label vs code name), and system of record. Mark each claim **verified** (read or ran it) or **inferred**, and cite file:line. Do not edit files. Do not guess business rules; list anything that looks like a rule as a question.

## Rules that matter

- **Only the PM can establish a `[target]`.** Never mark something target because the code does it. Code shows current state; the PM confirms intent.
- **Tags in prose:** `[current]` verified by reading or running code; `[target]` the model the business is building toward; `[confirm]` inferred or unverified (say "I think"). Anything not run is `[confirm]` or "read from code, not run".
- **Two separate status axes, never collapse them.** `realization` (where it lives: modeled, fragmented, conceptual) and `versioning` (how repeated runs are handled: none, implicit, explicit). A well-modeled table can still have no "current" marker; that is versioning, not fragmentation. When the PM says "fragmented", ask which they mean. Allowed values are defined in `validate.py`.
- **Name collisions are the main output.** Build a disambiguation table of everything the UI calls by one name. Every card has `ui_labels`.
- **Abstract concepts are legitimate.** If no model exists, mark it `conceptual`, list stand-ins, write design questions, do not invent structure.
- **A missing concept shows up as a gap.** When several consumers each re-derive "the one set" differently, ask whether a concept is missing.
- **Respect scope calls.** Drop deprecated features and out-of-scope systems everywhere, including notes (use `--removed`).
- **Missing relationships:** if the business model has an edge that code lacks, record a `target` edge and say what is missing in `note`.
- Worked examples are illustrative; label them. No emoji, sentence case, plain hyphens.

## Card skeleton

Quote any frontmatter value containing a colon or starting with a special character. `related` lists main relationships only; `graph.yaml` is complete.

```markdown
---
concept: Order                       # PascalCase, equals the graph node id
realization: modeled
versioning: implicit
aliases: []
ui_labels: []                        # what screens call it, if different
not_to_be_confused_with: []          # concept ids (non-concepts only warn)
system_of_record: none               # or the store and table
code_names: []                       # tables, models, routes, enums, hooks
identity: "how one instance is identified"
related:
  - { concept: Customer, cardinality: "many-to-one", status: current }   # current | target | confirm
---

## Definition
One or two plain sentences. If abstract or nonexistent, say so in bold directly under it.

## What it is NOT
Boundaries and the most common misreadings. Highest-value section.

## Business invariants
- MUST / MUST NOT rule. [current]   (every item tagged [current], [target] or [confirm])

## Current realization
Exact names from code. Small tables, not pasted schemas.

## Known modeling tensions
Open problems, with file:line cites for load-bearing claims.

## Design questions
Optional, only for concepts with open modeling decisions. Questions, not decisions.

## Worked example
One realistic instance. Illustrative.

## Common agent mistakes
What a new engineer or agent would get wrong.
```

`graph.yaml` lines:

```yaml
title: Acme ontology graph   # optional, shown on the viewer page
nodes:
  - { id: Order, card: order.md, realization: modeled, versioning: implicit, home: billing_service, note: "one line" }
edges:
  - { from: Order, rel: placed_by, to: Customer, cardinality: "many-to-one", status: current, note: "evidence or gap" }
```

`home` is the system where the concept lives, named as in the repo's architecture docs, or `none`. `rel` is a snake_case verb phrase.

## Consistency read (manual, the script cannot do this)

Cardinalities agree across a card, its counterpart and the graph; the same fact is not stated differently in two cards; aliases do not collide with other concepts' names. Fix, then re-run validate.

## Finish

Report the biggest gaps found, the open questions for the PM, and the count of remaining `[confirm]` items (validate prints it). Someone named by the PM must clear `[confirm]` items before the ontology counts as agreed. Then offer to commit on a correctly named branch. A change to the architecture doc is out of scope unless the PM asks.
