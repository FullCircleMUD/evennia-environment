# Test plan

Every test case the library commits to covering, and the test function that covers it. The library is
built test-first: cases are agreed here, tests are written against them, then the implementation is
written to pass. The **Test function** column is the auditable trail — it is filled in as each test is
written, so an empty cell means the case is agreed but not yet covered.

Case IDs are stable and referenceable. Do not renumber; retire an ID rather than reuse it. Every test
function carries its case ID as its docstring, so the trail reads in both directions.

All test functions live in `src/evennia_environment/tests.py`.

**Nothing but the scaffold is planned yet.** The behaviour is still being designed — see
[Open decisions](#open-decisions) below. Cases land here as each surface is agreed, and no code is
written before they do.

| Prefix | Covers |
|---|---|
| `SC` | The scaffold — the package installs and the runner runs |

## Fixtures

None beyond the scaffold case. The fixtures table is filled in with the first real surface: it names
the fake objects the suite needs and what each is for.

## SC — the scaffold

| ID | Case | Test function |
|---|---|---|
| SC-01 | The package imports and reports its version | `test_sc_01_package_imports_and_reports_its_version` |

## Open decisions

What has to be settled before the first behavioural case can be written. Each is a question raised in
the design conversation and left open, not a gap to be filled by whoever reads this next.

**Terrain**

- `[TBD — needs discussion: how a consumer declares its terrain types. The shape put up was
  evennia-equipment's — an enum in the consumer's own module and a setting naming its dotted path,
  with the effects declared against it. Not yet approved.]`
- `[TBD — needs discussion: how a room carries its terrain. A mixin, an attribute, a tag, or a
  world-builder field were all possible; none was chosen.]`
- `[TBD — needs discussion: whether a room with no terrain falls back to every key's registered
  default, or whether the consumer nominates a fallback terrain so an untagged room is visibly a
  mistake.]`
- `[TBD — needs discussion: whether a terrain's effects vary by phase of day, as weather's do. The
  desert case that forced per-phase payloads for weather may or may not reach terrain.]`

**The effect vocabulary**

- `[TBD — needs discussion: whether `register_effect` carries the merge kind from the start, for
  weather to use later, or gains it when weather lands. Terrain alone never merges — a room has one
  terrain — so the field is unused until then, and adding it later rewrites every consumer's
  registrations.]`

**Weather**

- `[TBD — needs discussion: how per-phase payloads sit against the calendar's six watches. The
  exploration assumed four phases; the calendar shipped six, so either a terrain authors six payloads
  or the unwritten ones inherit.]`
- `[TBD — needs discussion: whether mountains are their own region or a terrain-driven index shift
  on a neighbouring one.]`
- `[TBD — needs discussion: whether exposure stays three tiers or becomes a scalar.]`

**The library**

- `[TBD — needs discussion: whether the library owns any tables. Nothing so far needs storing —
  terrain is declared and weather is derived from the day number — but this has not been ruled on.]`
- `[TBD — needs discussion: whether the terrain tables are authored in YAML through
  `evennia-yaml-reader` as well as in Python. Registration is the substrate either way; a loader is
  additive and does not block the first cases.]`

**Where this came from.** The design conversation is summarised in the umbrella's
`ops/scratch/weather-library-exploration-2026-09-10.md`, which is a brainstorm and says so. Nothing
in it is agreed. Treat a shape lifted from it as an invention until it has been discussed here.
