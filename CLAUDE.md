# CLAUDE.md

> **Project-wide working rules and cross-repo context live in the FCM umbrella repo's `CLAUDE.md`**,
> loaded automatically when you work from the umbrella root. If you opened this repo directly instead
> of via the umbrella, relaunch from the umbrella root for the full context. This file holds only this
> repo's specific instructions.

Instructions for Claude (and other LLM agents) working in this repository.

## What this project is

`evennia-environment` makes a room's surroundings mechanical rather than decorative — terrain that is
permanent and weather that varies, both answering the same questions to whatever call site asks.
Tagline: **"What a room's surroundings do to whoever is standing in it."**

**The library holds two contributors to one answer.** Terrain belongs to the room and never changes.
Weather is derived from the calendar and varies by day and season. They share one vocabulary, so a
call site asks for `move_cost` once and does not care which of them supplied it.

**Terrain and weather live in one library, not two.** A terrain-only library is a registry, a lookup,
a default and a mixin — not enough to carry the library-standards overhead. It could not live in
FCM's game code either, because weather depends on it and weather has to stay game-agnostic. Do not
reopen the split.

## Project status

Feature complete as the requirements are currently understood, and expected to be improved
iteratively as early development of the game uncovers more.

## Where to read first

1. [docs/test-plan.md](docs/test-plan.md) — the cases the library commits to, and § Open decisions for
   what is unresolved. **A behavioural change starts here**, not in the code.
2. [docs/design.md](docs/design.md) — how it is put together, and why.
3. [docs/installing.md](docs/installing.md) — what a consumer declares, with a worked example.

[docs/INDEX.md](docs/INDEX.md) maps the rest.

## Load-bearing architectural principles

Every implementation decision must respect them.

1. **The library does not own game concepts.** Hit points, thirst, encumbrance, light sources and what
   a swamp is *for* belong to the consumer game. The library carries effect keys the consumer named
   and values the consumer chose.

2. **No FCM-specific assumptions.** FCM is the first consumer. Its terrain names, its effect keys, its
   movement rules and its regions all stay in FCM. Default to "consumer concern" when uncertain.

3. **Test-first.** A case lands in [docs/test-plan.md](docs/test-plan.md), then the test, then the
   code. See [test-first-process.md](../../design/test-first-process.md) for the process and the
   rationale.

4. **The consumer declares the vocabulary; the library never invents a key.** A game declares the
   effect keys it will use and the default for each. Terrain and weather then supply values against
   those keys, and the game's own code reads them and decides what they mean. If a hit point ever
   appears in this library's tests, the boundary has leaked.

5. **A contribution is a callable the library routes, not a value it computes.** An effect holds
   `f(value, **kwargs) -> value`. A declared number cannot express most of what a game wants —
   natural light is terrain and the hour together — so the consumer writes the function and the
   library never decides what a value means. The static case is a stock helper, so there is one shape
   and one code path. Validation is what a declared value would have bought: the signature is checked
   with `inspect` at the line declaring it, and the answer against the effect type's `return_type` at
   every step of resolution.

6. **Values are pulled, not pushed.** A call site asks the room what it contributes, at the moment it
   is already doing something. That is what lets movement price a room before entering it rather than
   charging on arrival — a query answers for any room, including one nobody is standing in.

7. **The library answers for a room; it does not decide which room to ask.** Whether traversing an
   exit charges for its origin, its destination or both is the consumer's movement rule. This is what
   keeps the library small, and the pressure to relax it will come from exits.

## Out of scope

- **Applying an effect.** The library returns a value. Deducting movement, dealing damage, dousing a
  torch and refusing a move are all the consumer's, and so is the tick that drives any of them.
- **Atmospheric prose as the point.** Weather carries messages, but a library that only prints them is
  a script and a message table. The mechanical effect is the reason this exists.
- **Equipment rust and spell-school modifiers.** Both were rejected. Do not re-propose either.

## Working conventions

- **Behavioural change starts in the test plan.** Add the case, write the test, then implement. Fill
  the **Test function** column when the test exists — it is a coverage claim and the linter checks it
  both ways.
- **Editing design docs.** Update or add design documents whenever an architectural decision is made
  or refined. Capture the *why*, not just the *what*. Index new docs in [docs/INDEX.md](docs/INDEX.md).
- **Don't put implementation detail in this file or README.** Link out to `docs/` instead. Keep
  `CLAUDE.md` and `README.md` stable; let `docs/` churn.
- **License.** BSD 3-Clause. Source files carry an SPDX header on the first line
  (`# SPDX-License-Identifier: BSD-3-Clause`).

## Documentation discipline (load-bearing)

**Every sentence must help a developer understand how the library works, or help a consumer implement
it. If it does neither, it does not go in.**

That rules out **measurements** — test counts, coverage figures, how many consumers or call sites
there are, how much is finished. Every one of them is wrong after the next commit, and none of them
changes what a developer or a consumer does next.

**Measurements have exactly one home: [docs/progress.md](docs/progress.md).** It is a cumulative,
dated log, so a snapshot of where things stood on a given day is what belongs there and does not go
stale — it was true when it was written and stays true as a record. Everywhere else, a number is a
claim about now, and now moves.

It does not rule out a **map**. The repository layout below is a file tree, and a file tree is how an
agent knows what is in here without walking the directory. It goes stale only when a module is added
or moved, and it earns that. The test is which of the two something is: a map of where things are, or
a claim about how much or how far.

**A section is as long as it has content for.** The nine standard sections are required; filling one
out is not. A sentence is a complete section when a sentence is all there is to say, and bullets beat
prose whenever the content is a list. Nothing is written to make a heading look inhabited.

**What each surface is for.** `CLAUDE.md` and `docs/design.md` answer a developer, human or LLM:
where things are, what they do, how they work and why they were built that way.
[docs/installing.md](docs/installing.md) answers a consumer, and answers concretely — what to add to
`INSTALLED_APPS`, every setting that has to be declared and what happens if it is not, what to do
about the database if anything, and what the library does not check for them.

Design documents in `docs/` must reflect decisions **actually discussed and agreed on with the project
owner**. They are not a place to forward-design the system from first principles or extrapolate
"reasonable defaults" from a starting point.

1. **Only capture what was discussed and agreed.** If the conversation establishes a principle, do not
   extrapolate it into specifics that were not raised — effect key names, terrain lists, band counts,
   setting names, defaults.
2. **Flag open questions explicitly.** Write `[TBD — needs discussion: <what is open>]` so a future
   session picks the topic up deliberately rather than inheriting an unagreed assumption.
3. **Smaller is better.** Three discussed points captured faithfully beat three discussed points plus
   seven invented ones. Resist filling out sections "for completeness".

**The tempting source of unasked-for answers is the exploration note this library came from** —
`ops/scratch/weather-library-exploration-2026-09-10.md` in the umbrella. It is a brainstorm, and it
says so at the top. A shape lifted from it is an invention unless it has been discussed here.

## Repository layout

```
evennia-environment/
├── CLAUDE.md                  # this file
├── README.md
├── LICENSE                    # BSD 3-Clause
├── pyproject.toml
├── runtests.py                # standalone test runner; no gamedir required
├── examples/                  # demo gamedirs for integration testing
├── docs/                      # design wiki (humans + LLMs)
│   ├── INDEX.md
│   ├── design.md
│   ├── installing.md
│   ├── interoperability.md
│   ├── progress.md
│   ├── test-plan.md
│   └── archive/               # historical context, not authoritative
├── src/
│   └── evennia_environment/   # library code (src layout)
│       ├── __init__.py        # what a consumer imports: the declarations, the helpers, resolve()
│       ├── apps.py            # AppConfig: runs the boot check, connects the calendar's signals
│       ├── config.py          # the settings accessors, and check_settings()
│       ├── effects.py         # EnvironmentEffectType and EnvironmentEffect
│       ├── helpers.py         # the stock helpers — Constant, Add, Multiply, Round*, Chain
│       ├── log.py             # binds environment_log via evennia-logging-extension
│       ├── refusal.py         # the one route a refusal takes: log at ERROR, then raise
│       ├── resolve.py         # default → terrain → weather, type-checked at every step
│       ├── room.py            # TerrainProperty and EnvironmentRoomMixin; imports Evennia
│       ├── terrain.py         # TerrainType
│       ├── tests.py           # unit tests, run via runtests.py
│       └── weather.py         # WeatherType, WeatherSlot, and the derived weather band
└── tests/                     # standalone test infrastructure and fixture modules
    ├── test_settings.py
    └── urls.py
```

`room.py` is not re-exported from `__init__.py`. It imports Evennia, and the package is imported
while Django is still building its app registry, so a consumer takes the mixin from
`evennia_environment.room` directly.

No `contrib/` — the standards forbid scaffolding one empty.

## Tools and environment

- **Tests use Django's test runner** via `python runtests.py`, which bootstraps Django then calls
  `evennia._init()`, as the siblings do. Not pytest, and no gamedir required.
- `tests/test_settings.py` installs `evennia_calendar` alongside this library, because weather reads
  the season and the phase from it. The fixture modules beside it are the declarations a consumer
  would write — a terrain enum, a terrain table, room typeclasses.
- Development uses a dedicated venv at `venv/` (gitignored), independent of any consumer game.

## Sibling libraries to reference

- **[../evennia-calendar/](../evennia-calendar/)** — a hard dependency. Its `season` and `phase`, and
  its `day_changed` / `phase_changed` signals, are what weather is derived from.
