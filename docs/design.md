# Design

How the library is put together, and why it is put together that way.

## The shape

A consumer declares four things. The library holds them, and answers questions against them.

| They declare | The library does |
|---|---|
| A terrain `Enum` | Validates what a room is assigned |
| `EnvironmentEffectType`s — the questions their game asks | Checks every answer against the declared return type |
| `WeatherType`s, each declaring what it changes | Runs its contribution when it is in force |
| `TerrainType`s, each with ten weather slots | Picks the slot the day's band names, and the hour picks that slot's weather |

Nothing else. The library names no effect, no terrain and no weather, and decides nothing about what
a value means.

## Two classes per idea: the declaration, and the thing with a value

`EnvironmentEffectType` says `move_cost` is a float defaulting to 1.0. `EnvironmentEffect` says what
one swamp, or one blizzard, does about it. The type is the vocabulary, declared once for the whole
game; the effect is one contributor's answer.

Collapsing them would mean every terrain redeclaring the key, with no single list to check against
and no way to catch a typo.

## A contribution is a helper, not a value

An effect holds a callable — `f(value, **kwargs) -> value`. A declared number cannot express most of
what a game wants: a stealth bonus depends on who is asking, an encumbrance penalty on what they are
carrying. So the consumer writes a function, and the library routes rather than computes.

The static case is a stock helper, so there is one shape and one code path:

```python
EnvironmentEffect(MOVE_COST, Constant(2.0))
EnvironmentEffect(MOVE_COST, Chain(Multiply(1.5), RoundUp()))
```

Whether a contribution replaces the running value or modifies it is its own choice — `Constant`
ignores what it was handed, anything else uses it. The library has no merge rule and needs none.

## Day and night are structural, not something a helper works out

An effect declares two helpers, and `resolve()` picks. Underground is dark at noon; a mountain pass
costs more to cross after dark; a desert freezes at night.

```python
EnvironmentEffect(NATURAL_LIGHT, Constant(True), night=Constant(False))
EnvironmentEffect(MOVE_COST, Constant(2.0), night=Constant(3.0))
```

A helper could read the clock itself, and that was the first shape considered. It hides the
dependency: nothing in the declaration says the value varies, so nothing can inspect it, a consumer
writing the same closure on every terrain repeats it, and a value that came from data could not
express it at all. Weather had structure for this from the start — a `WeatherSlot` holds a day
weather and a night one — and an effect having it too is the same answer applied to the other
contributor.

`night` is optional and filled from the day helper when it is not given, so a contribution that does
not vary declares exactly what it declared before. Both halves are always populated, which is what
keeps absence out of everything downstream, and "does this vary" is `night is helper`.

**The pair sits inside the effect, not around the collection.** One key is still one effect, so the
rule below holds and the chain stays two links. Two sets of effects per contributor would have needed
a rule for a key declared in one and not the other.

## Nothing is dark because it is night

`is_night()` reads the clock. It answers the same everywhere in the game, and the setting behind it —
`ENVIRONMENT_NIGHT_WATCHES` — is a list of watch numbers.

Whether a *place* is dark is a different question: a cavern is dark at noon, a blizzard darkens a
valley at dusk. That one is terrain and weather together, and a consumer asks it as an effect key
they declared. Naming the clock for darkness put both under one word, and a consumer reaching for the
watches to light a room would have got the wrong answer for every cave.

## Two kwarg names are the library's

`effect_type` and `terrain_type` are refused as caller kwargs. Both are taken positionally, so one of
that name collides with the parameter and Python raises before either function runs a line — naming
an argument the caller never passed, from a call where no terrain is visible.

Refused rather than allowed through. A helper handed `terrain_type` would reasonably read it as *the*
terrain, which is the room's and not the caller's to supply.

The check sits in the room accessor, which is the only place a caller's kwargs are still separate
from the positional arguments, and the accessor takes its effect type positional-only so a kwarg of
that name reaches the check rather than Python's error.

## Pull, not push

A call site asks a question at a moment it was already running, and acts on what comes back. The
library never reaches out and changes an object.

That is what lets movement price a destination nobody is standing in — asking is free, so a command
can cost every exit before choosing one. A contribution that acted would make that unsafe.

A consumer's helper is their code and can do what they write. The library's contract is the returned
value, and the docs say a helper that changes things makes a query unsafe.

## At most one contribution per key per contributor

A terrain declares one effect for `move_cost`; so does a weather. A second is refused at the
declaration.

That single rule is what removes the ordering problem. The chain is never longer than two, so the
order is `default → terrain → weather` and there is nothing to configure: no priorities, no operation
kinds, no tiebreaks. A helper is arbitrary code, so anything an author would express as three ordered
steps they write inside one function, in the order they wrote the lines.

## Resolution

```python
night = is_night()
weather = current_weather(terrain_type, night)

value = effect_type.default(None, **kwargs)
if terrain declares this key:  value = terrain_effect.helper_for(night)(value, **kwargs)
if weather declares this key:  value = weather_effect.helper_for(night)(value, **kwargs)
```

`resolve()` is given a terrain and finds the rest. The hour is read once at the top and used for
everything that depends on it — which of a slot's two weathers is in force, and which half of each
contribution runs. The weather is worked out once and reused.

**One question, one place.** The alternative was the room accessor working out the hour, collapsing
the slot itself and passing a weather down. That put the same decision in two places: terrain's half
picked inside `resolve()`, weather's picked outside it. Reading the calendar here is what that costs
— `resolve()` is not callable with nothing running. `_fold()` underneath takes everything it needs as
arguments and stays a plain function.

**A terrain is always given.** A room with none of its own resolves against `NO_TERRAIN`, so absence
is answered before `resolve()` is reached and nothing on the path asks whether a terrain is there.

The return type is checked after every step rather than once at the end, so a refusal names which
helper got it wrong instead of leaving three candidates.

Declaring nothing is how a terrain or weather says it changes nothing. Silence leaves the default's
answer standing, so a table is sparse and a game answers every question before any content exists.

## Weather is derived, never stored

One number a day for the whole game: `sha256(seed:day) % 6`, floored at three, shifted by the season.
Nothing is in the database, no two processes coordinate, and any day past or future can be asked for.

The season's shift is what widens six values into the ten slots a terrain has:

| Season | Shift | Range |
|---|---|---|
| Winter | −2 | 1 – 6 |
| Spring, Autumn | 0 | 3 – 8 |
| Summer | +2 | 5 – 10 |

So slots 1 and 2 are reachable only in winter and 9 and 10 only in summer. A mountain snows in winter
and its clear summer day never happens in winter. Repeating a weather across slots weights it.

Python's own `hash()` is unusable here: randomised per process for strings, so two processes would
disagree, and the identity for small ints, so `hash(day) % 6` is a metronome.

## Held between signals, not polled

The band and whether it is night are both held in module state. `day_changed` refreshes the band and
`phase_changed` refreshes the hour, and a read computes only when nothing is held — which is what
answers between a restart and the next rollover.

Measuring decided this: `game_date()` costs about 3,600 ns against the hash's 514, so the saving is
in not asking the calendar on a read rather than in caching the hash.

Neither value is worth surviving a reload, and a reload restarts the process anyway.

## What a room stores

One string. `terrain = "swamp"` in Evennia's string column, and nothing else.

The member goes in and comes back — `at_set` takes `Terrain.SWAMP` or `"swamp"`, `at_get` resolves it
— so a consumer reads a member while the database holds text a YAML file can write and a query can
search on. A `TerrainType` could not be stored anyway: it holds callables, and pickle refuses them.

Write-once, because a room is given its terrain when it is built and does not change it in play.

## A room with no terrain resolves against a null one

`terrain_type` never answers `None`. A room with nothing assigned, and a room carrying a member no
`TerrainType` was declared for, both get `NO_TERRAIN` — an empty terrain the library declares, with
no effects and ten slots of an empty weather.

Every key then falls through to its own default, which is the answer an absent terrain gave anyway.
What it buys is that nothing downstream tests for absence: `resolve()`, both weather accessors and
the description accessor each lost a branch.

It is a null object rather than content — no effect key, no effect, no game concept. `room.terrain`
still answers `None`, so a builder asking which rooms still need one keeps the signal.

## Everything that raises, logs

Every refusal in the library writes to `environment.log` at ERROR before it raises. There is no
refusal a consumer can hit that leaves nothing behind.

The rule exists because the exception alone reaches whoever is standing in front of a console, and
that is rarely the person troubleshooting. A world build applies content to hundreds of rooms and may
catch per room and carry on; `resolve()` is reached from tickers and scripts with no command handler
to catch anything. The file is what is still there an hour later, and what a consumer can be asked to
send.

Three routes, by what each raises:

| Route | Raises | For |
|---|---|---|
| `config._refuse()` | `ImproperlyConfigured` | The boot check. Every problem found, one per line |
| `refusal.refuse()` | `ValueError` | A declaration the consumer wrote wrong, and `resolve()`'s two |
| `refusal.refuse_attribute()` | `AttributeError` | A refused assignment to a room's `terrain` |

**Routing rather than a log call beside each raise.** A log call per raise site would need a delivery
case per raise site to be sure none was missed, and the next one added would slip through anyway. One
route needs one case, and a test reading the parsed source holds it closed.

**The boot refusal logs more than it raises.** A `raise ... from` takes one cause, so the exception
chains the first; the file takes every broken module's traceback and gets all of them. A consumer
whose declaration module will not import needs the line that broke, not `could not be loaded`.

**A room's refusal names the room** — key and dbref both, since two rooms can share a key. Without it
a build gives back the bad value and nothing to search for.

**Repeats are not suppressed.** `resolve()` is on the per-action path, so one broken helper writes a
line for every call that reaches it. That volume is the signal: a log filling with one refusal is how
a consumer finds out they have something to fix. Suppression would be code carried for the life of
the library to make a symptom quieter.

## What is deliberately not here

- **Applying an effect.** Deducting movement, dealing damage, dousing a torch and refusing a move are
  the consumer's, and so is the tick that drives any of them.
- **Regions.** A terrain's ten slots are the whole of where weather comes from.
- **An operation vocabulary the consumer must use.** The stock helpers are tools; a consumer's own
  function is a first-class contribution.
- **Anything FCM.** Its terrains, its effect keys and its movement rules all stay in FCM.
