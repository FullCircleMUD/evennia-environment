# Current thinking and progress

Where the design has got to and what is built, written so a session picking this up in a fortnight can
start from here. [test-plan.md](test-plan.md) is the authority on cases and open decisions; this page
carries the reasoning behind them and the state of the work.

## What the library is

Terrain and weather in one library. **Terrain** is permanent and belongs to the room. **Weather**
varies with the calendar and belongs to the region. Both answer the same question — what does this
room contribute — through effect keys the consumer declares.

They are one library because a terrain-only library is a registry, a lookup, a default and a mixin,
which does not carry the library-standards overhead. It could not live in FCM's game code either,
because weather depends on it and weather has to stay game-agnostic.

## The shape of the design

The consumer declares three things in one module, and one setting names that module:

- their terrain types, as an `Enum`
- their effects, registered against the library's master list
- the values each terrain gives for the effects it overrides

The library never invents an effect key and never applies a value. It knows keys exist, what each
defaults to, and what type it is in. What a value *means* is decided in the consumer's own code — the
movement command, the survival tick, the look command.

### Why it is declarative

The consumer hands over data, not callables. Data can be validated at boot and tested exhaustively; a
callable inside the lookup could be neither, and nothing raised so far needs one.

### Values are pulled, not pushed

A call site asks a room what it contributes, at the moment it is already doing something. That is what
lets movement price a room *before* entering it rather than charging on arrival — a query answers for
any room, including one nobody is standing in. Charging on arrival is what produces a character with
minus one movement point.

### The library answers for a room, not for a move

Whether traversing an exit charges for its origin, its destination or both is the consumer's movement
rule. This is what keeps the library small, and the pressure to relax it will come from exits.

### Terrain is the base, weather is the modifier

There is no merge algebra. A swamp's movement cost is the number the author wrote — not
`Multiply(2.0)` against some notional plains. Terrain and weather are not symmetric contributors to
one key, so nothing needs an order-independent merge, and `Effect` carries no merge kind.

How weather modifies the base is a weather decision, taken when weather is built.

### Effects resolve at read time

A room stores a reference to its terrain, never a copy of the values. Change a terrain's numbers and
every room of that terrain answers differently on its next query — nothing to migrate, nothing to
walk. Do not add a per-room cache: Evennia's idmapper holds typeclass instances for the life of the
Server process, so a cached value's staleness window is unbounded.

## Two things that were tested, not assumed

- **An `Enum` whose values are effect dicts silently aliases.** Two terrains declaring equal effects
  become one member — `JUNGLE` turns into a second name for `FOREST`. This is why the terrain `Enum`
  holds plain strings and the effects are declared separately.
- **Evennia's `dbserialize` round-trips an `Enum` member with identity intact.** So a room can store
  `Terrain.SWAMP` itself rather than a string.

## What is built

| Surface | State |
|---|---|
| Repo scaffolding, test runner, docs surfaces | Done, committed and pushed |
| `Effect(key, datatype, default)` | Done — 12 cases, `EF` |
| `EffectRegistry`, `register()`, `get()` | Done — 8 cases, `ER` |
| Everything else | Not started |

21 tests passing via `python runtests.py`. The venv is at `venv/`, with Evennia, the library and both
sibling dependencies installed editable.

**Uncommitted:** everything after the bootstrap commit — `effects.py`, its tests, and the `EF` and
`ER` sections of the test plan.

### The rules the built code follows

- `Effect` validates itself in `__post_init__` and raises a `ValueError` there. A malformed
  declaration is the consumer's code failing at their own line; a traceback pointing there beats a
  tidy list pointing at us. Boot-time collection is for `check_settings()`, not this.
- The default is checked with `isinstance` and nothing more — no coercion, no widening. Declare
  `float`, write `1.0`. `None` is the one exemption, and what it means is the consumer's.
- A bool default passes an `int` datatype, because `isinstance(True, int)` is `True` in Python. That
  follows from the rule rather than being chosen; `datatype=bool` is how a consumer means a boolean.
- `register()` refuses a key already declared differently, and passes silently on an identical
  re-registration so a re-imported module is harmless.
- `get()` returns the `Effect` or `None`. `None` is an ordinary answer: validating a terrain means
  asking about keys that may not be registered.

## The next chunk — `check_settings()`

Boot is where the consumer's module gets imported and everything gets checked. Agreed so far:

- The library imports the consumer's declaration module itself, during `ready()`, so registration
  happens at a known moment rather than whenever something touches a module.
- An invalid declaration means the game does not start. Fix it before the game runs.
- Success is observable primarily by the game starting, plus one log line — `7 effects registered` —
  at INFO, or at WARN when the count is zero.
- An empty registry is not a refusal. It has a correct reading (nothing declared yet) and refusing
  would punish someone booting to check their install before writing content.

Open within it: whether registration closes once boot validation has run.

## After that

In rough order, and each one a discussion before it is a test plan:

1. The terrain-to-effects table — registered like effects, or a consumer-authored dict validated at
   boot.
2. The room mixin: `at_set()` validating the terrain, accepting the `Enum` member or its string value
   so YAML-authored world content resolves at the assignment.
3. The accessor a call site uses.
4. Weather.

Everything still undecided is in [test-plan.md](test-plan.md) § Open decisions, with the question
stated rather than a gap left to be filled.

## How to work on this

**One surface at a time, and no more than was asked.** The scope discipline here is strict: cases get
written for the surface under discussion and nothing beyond it. A read API justified by a caller that
does not exist yet is the failure mode to watch for — it happened once already, with membership,
iteration and a builder command invented to justify making the registry a `Mapping`.

**The order is test plan, then approval, then tests, then code.** Not a suggestion — see
[test-first-process.md](../../../design/test-first-process.md).

**The exploration note this library came from** — `ops/scratch/weather-library-exploration-2026-09-10.md`
in the umbrella — is a brainstorm and says so at the top. A shape lifted from it is an invention until
it has been discussed.

## Outstanding warnings

`python3 .claude/skills/library-standards-linter/lint_library.py libraries/evennia-environment` from
the umbrella reports four, none of them errors:

| Warning | State |
|---|---|
| `constant_outside_config` | `EFFECTS` is declared in `effects.py`. The standard wants it in `config.py`, re-exported from `__init__.py`. Undecided — it would create `config.py` a chunk before there is a setting for it |
| `interop_missing_sibling` | `fcm-subscriptions` appeared in `libraries/` and needs a section in [interoperability.md](interoperability.md) |
| `installing_no_steps` | Two steps, wants three. Clears when there is a setting to declare |
| `log_shim_unused` | Nothing is logged yet. The boot line is what will retire it — `Effect` should not log, since a refusal raises at the consumer's own line and logging before dying is noise |
