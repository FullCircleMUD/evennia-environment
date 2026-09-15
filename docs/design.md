# Design

How the library is put together, and why it is put together that way.

## The shape

A consumer declares four things. The library holds them, and answers questions against them.

| They declare | The library does |
|---|---|
| A terrain `Enum` | Validates what a room is assigned |
| `EnvironmentEffectType`s — the questions their game asks | Checks every answer against the declared return type |
| `WeatherType`s, each declaring what it changes | Runs its contribution when it is in force |
| `TerrainType`s, each with ten weather slots | Picks the slot the day's band names |

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
what a game wants: natural light is terrain and the hour together, a stealth bonus depends on who is
asking. So the consumer writes a function, and the library routes rather than computes.

The static case is a stock helper, so there is one shape and one code path:

```python
EnvironmentEffect(MOVE_COST, Constant(2.0))
EnvironmentEffect(MOVE_COST, Chain(Multiply(1.5), RoundUp()))
```

Whether a contribution replaces the running value or modifies it is its own choice — `Constant`
ignores what it was handed, anything else uses it. The library has no merge rule and needs none.

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
value = effect_type.default(None, **kwargs)
if terrain declares this key:  value = terrain_helper(value, **kwargs)
if weather declares this key:  value = weather_helper(value, **kwargs)
```

`resolve()` takes the contributors as arguments rather than finding them, so answering needs no room,
no database and no Evennia. The room mixin is a thin wrapper that finds both and delegates. Refusing
reaches the log, so that path does need Evennia.

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

The band and whether it is night are both held in module state. `day_changed` and `phase_changed`
refresh them, and a read computes only when nothing is held — which is what answers between a restart
and the next rollover.

Measuring decided this: `game_date()` costs about 3,600 ns against the hash's 514, so the saving is
in not asking the calendar on a read rather than in caching the hash.

Neither value is worth surviving a reload, and a reload restarts the process anyway.

## What a room stores

One string. `terrain = "swamp"` in Evennia's string column, and nothing else.

The member goes in and comes back — `at_set` takes `Terrain.SWAMP` or `"swamp"`, `at_get` resolves it
— so a consumer reads a member while the database holds text a YAML file can write and a query can
search on. A `TerrainType` could not be stored anyway: it holds callables, and pickle refuses them.

Write-once, because a room is given its terrain when it is built and does not change it in play.

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
