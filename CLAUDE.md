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
Weather is derived from the calendar and varies by day, season and region. They share one vocabulary,
so a call site asks for `movement_cost` once and does not care which of them supplied it.

**The name was chosen against `evennia-terrain` and `evennia-weather` as separate libraries.** A
terrain-only library is a registry, a lookup, a default and a mixin — not enough to carry the
library-standards overhead. It could not live in FCM's game code either, because weather depends on it
and weather has to stay game-agnostic. So both live here, terrain first. Do not reopen the split.

For the big-picture overview, read [README.md](README.md).
For the design wiki, read [docs/INDEX.md](docs/INDEX.md).

## Project status

**The effects vocabulary is built; terrain and weather are not.** `EnvironmentEffectType` and
`ENVIRONMENT_EFFECT_TYPES` — the shape a consumer declares one effect type in, and the list they
declare it to — are done and tested. Everything else is open:
[docs/current-thinking-and-progress.md](docs/current-thinking-and-progress.md) is where a session
picks the work up, and [docs/test-plan.md](docs/test-plan.md) carries the cases and the open
decisions.

There is no `config.py` and no `apps.py` yet, deliberately. Both exist to check settings, and no
setting has been agreed. They land with the first one.

## Where to read first

1. [docs/test-plan.md](docs/test-plan.md) — the cases the library commits to. **A behavioural change
   starts here**, not in the code. **Start here.**
2. [README.md](README.md) — what the library is and its status.
3. [docs/INDEX.md](docs/INDEX.md) — map of all design docs.
4. [docs/installing.md](docs/installing.md) — what a consumer declares.
5. [docs/interoperability.md](docs/interoperability.md) — this library against its siblings.

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

4. **The consumer declares the vocabulary; the library never invents a key.** A game registers the
   effect keys it will use and the default for each. Terrain and weather then supply values against
   those keys, and the game's own code reads them and decides what they mean. If a hit point ever
   appears in this library's tests, the boundary has leaked.

5. **Everything is declarative — the consumer never hands the library a callable to run.** Declaring
   the vocabulary and consuming the values are both the consumer's, and both are late-bound. What
   sits between them is data the library can validate at boot and test exhaustively. A callable
   inside the lookup would cost both, and nothing raised so far needs one.

6. **Values are pulled, not pushed.** A call site asks the room what it contributes, at the moment it
   is already doing something. That is what lets movement price a room before entering it rather than
   charging on arrival — a query answers for any room, including one nobody is standing in.

7. **The library answers for a room; it does not decide which room to ask.** Whether traversing an
   exit charges for its origin, its destination or both is the consumer's movement rule. This is what
   keeps the library small, and the pressure to relax it will come from exits.

## Out of scope

Decided as questions arise. Rulings so far:

- **Applying an effect.** The library returns a value. Deducting movement, dealing damage, dousing a
  torch and refusing a move are all the consumer's, and so is the tick that drives any of them.
- **Equipment rust and spell-school modifiers.** Both were raised and rejected — rust is a nuisance
  players route around, and spell-school weighting is a balance rabbit hole.
- **Atmospheric prose as the point.** Weather carries messages, but a library that only prints them
  is a script and a message table. The mechanical effect is the reason this exists.

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

Design documents in `docs/` must reflect decisions **actually discussed and agreed on with the project
owner**. They are not a place to forward-design the system from first principles or extrapolate
"reasonable defaults" from a starting point.

**Rules:**

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
├── .gitignore
├── examples/                  # demo gamedirs for integration testing; empty so far
├── docs/                      # design wiki (humans + LLMs)
│   ├── INDEX.md
│   ├── installing.md
│   ├── progress.md
│   ├── test-plan.md
│   ├── interoperability.md
│   └── archive/               # historical context, not authoritative
├── src/
│   └── evennia_environment/   # library code (src layout)
│       ├── __init__.py
│       ├── log.py             # binds environment_log via evennia-logging-extension
│       └── tests.py           # unit tests, run via runtests.py
└── tests/                     # standalone test infrastructure
    ├── __init__.py
    ├── test_settings.py
    └── urls.py
```

No `contrib/` — nothing opt-in exists, and the standards forbid scaffolding one empty. A room mixin
is the anticipated first candidate.

`tests/test_settings.py` installs `evennia_calendar` alongside this library, because weather reads
the season and the phase from it.

## Tools and environment

- Python 3.10+ (pinned via `pyproject.toml`).
- Runtime dependencies: Evennia, `evennia-logging-extension`, `evennia-calendar`.
- **Tests use Django's test runner** via `python runtests.py`, which bootstraps Django then calls
  `evennia._init()`, as the siblings do. Not pytest, and no gamedir required.
- Development uses a dedicated venv at `venv/` (gitignored), independent of any consumer game.

## Sibling libraries to reference

- **[../evennia-calendar/](../evennia-calendar/)** — a hard dependency, and the closest reference
  shape for repo structure, the test runner and the docs surfaces. Its `season`, `phase` and
  `season_changed` / `phase_changed` signals are what weather is built on.
- **[../evennia-equipment/](../evennia-equipment/)** — the reference for consumer-declared
  vocabulary: an enum in the consumer's own module, a setting pointing at it, the library validating
  both sides against that one list. Terrain follows the same shape.
- **[../evennia-survival/](../evennia-survival/)** — a likely consumer. Its meters are the mechanic
  that would first read an environment effect.
