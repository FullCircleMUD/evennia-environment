# Interoperability

This library against every sibling library in `libraries/`, including itself. A reader deciding
whether two of our libraries can be co-installed gets a definite statement from either side rather
than inferring from silence.

Each section names the relationship — **hard dependency**, **optional integration**, **indirect
dependency**, or **no coupling** — followed either by the constraints that apply or by an explicit
clearance stating *why* it is clear in terms of what this library does. "No known issues" is not a
clearance.

**The library is scaffolded and implements nothing**, so most clearances below rest on that rather
than on a design decision. They are provisional in the strongest sense: re-read every one of them as
each surface lands. What is already settled is that the library holds two contributors — terrain,
declared by the consumer, and weather, derived from the calendar — and answers questions about a
room rather than acting on one.

**A recurring theme, stated once.** Several siblings are ones a consumer would plausibly *compose*
with this library — hunger that rises faster in the heat, spawning that changes in a storm, an NPC
prompt carrying the weather. Composition in a consumer's own code is not a coupling: it needs no
import in either direction and constrains neither library. Where that is the whole of the
relationship, the section says so.

## evennia-ai-memory

**No coupling.** Neither library imports the other. ai-memory owns tables on an alias of its own;
whether this library owns any table at all is still open, and it issues no ORM writes today. An NPC
prompt carrying the weather is composition in the consumer's code.

## evennia-archive

**No coupling.** Neither library imports the other. Archive clones Evennia's schema so a character
can survive a world rebuild. Terrain is declared in the consumer's own code and weather is derived
from the day number, so neither is state a rebuild could take.

`[TBD — needs discussion: whether a room's terrain assignment is world content that a rebuild
re-creates. That is settled by how a room carries its terrain, which is open — see
[test-plan.md](test-plan.md) § Open decisions.]`

## evennia-calendar

**Hard dependency.** Weather is derived from the calendar: the day number keys the daily value,
`season` selects the band and the clamp, and `phase` selects the payload. The library also subscribes
to `season_changed` and `phase_changed` rather than running a clock of its own. `pyproject.toml`
declares it and `tests/test_settings.py` installs it.

Nothing flows the other way. The calendar knows nothing about weather, and its own
`interoperability.md` records the weather layer as a dependant rather than a dependency.

The calendar's constraints are the calendar's, documented there and not restated here. The one worth
naming because it reaches this library directly: two independently-installed instances measure game
time from different first-start timestamps and will disagree about the date — and therefore about the
weather. See [the calendar's installing.md](../../evennia-calendar/docs/installing.md) § Evennia's
time settings.

## evennia-database-cascade

**No coupling** today. This library owns no tables, needs no alias and ships no router.

`[TBD — needs discussion: whether the library owns any tables at all. Nothing so far needs storing.
If that changes, the cascade is how the alias is declared, and this section becomes a hard
dependency.]`

## evennia-environment

This library.

## evennia-equipment

**No coupling.** Neither library imports the other. Equipment governs what an object wears and
carries; this library answers questions about a room. Clothing that protects against exposure is the
obvious composition, and it is the consumer's code reading an effect value and consulting what is
worn — neither library needs the other to do it.

Worth knowing rather than a constraint: equipment's wear-slot declaration is the shape terrain is
being modelled on — an enum in the consumer's own module, a setting naming its path, the library
validating both sides against that one list.

## evennia-llm-service

**No coupling.** Neither library imports the other. llm-service dispatches model calls off the
reactor thread; this library does lookups and arithmetic and dispatches nothing. Putting the weather
into an NPC prompt is composition in the consumer's code.

## evennia-logging-extension

**Hard dependency.** `log.py` binds `environment_log` through its `make_logger`, and every line the
library emits goes through that binding to `environment.log`. The library does not run without it —
`pyproject.toml` declares it. Nothing flows the other way.

## evennia-message-bus

**No coupling.** Neither library imports the other. The bus coordinates state between processes;
weather is derived from the day number, so every process computes the same answer without
coordinating and there is nothing to publish. That is inherited from the calendar's design and holds
only while weather stays derived rather than rolled.

## evennia-mob-spawner

**No coupling.** Neither library imports the other. Spawning that varies with the weather is an
anticipated pattern and one of the reasons this library exists, but it is the consumer composing two
libraries: the spawner asks for an effect value and decides what to do with it.

## evennia-portal-multiplex

**No coupling.** Neither library imports the other. Multiplex operates at the Portal/Server transport
layer; this library answers questions inside the Server process and touches no connection.

The clock synchronisation that multiplex owns for the calendar reaches this library second-hand:
instances that disagree about the date disagree about the weather. That constraint belongs to the
calendar and is documented there.

## evennia-scaling

**No coupling.** Neither library imports the other. Terrain is declared in the consumer's code, which
every instance loads identically, and weather is derived from the clock — so a character moving
between instances carries no environment state and each instance answers the same way without being
told.

## evennia-shards

**No coupling.** Neither library imports the other. `evennia-scaling` is the standard for
multi-instance deployment and the section above is the one that applies; this entry exists because
the template covers every sibling.

## evennia-survival

**No coupling.** Neither library imports the other, and the design intent is that they stay that way:
survival steps its meters on its own clocks and asks this library for a rate when it does. Thirst
rising faster in the heat is the consumer wiring one to the other, not either importing the other.

The calendar's own `interoperability.md` left this open from its side. Answering it from here: **the
consumer composes them.** A direct coupling would mean this library naming a meter, which breaches
its first principle.

## evennia-targeting

**No coupling.** Neither library imports the other. This library declares no `p_`, `f_` or `op_`
callables and has no `targeting.py`.

`[TBD — needs discussion: visibility. Search and perception predicates are a plausible consumer of a
visibility range, which would make targeting a dependency. Nothing is designed yet.]`

## evennia-world-builder

**No coupling** today, and this is the pairing most likely to change. World-builder writes rooms and
exits from YAML, and a room's terrain is exactly the kind of field a builder would author there.

`[TBD — needs discussion: how a room carries its terrain — see [test-plan.md](test-plan.md) § Open
decisions. If the answer is a world-builder field, this section becomes a real relationship and the
constraint is documented by whichever library owns the field.]`

## evennia-yaml-reader

**No coupling** today. yaml-reader depends only on `pyyaml`, has no Evennia dependency and touches no
database.

`[TBD — needs discussion: whether terrain and weather tables are authored in YAML as well as in
Python. Registration is the substrate either way; a YAML loader would make this a hard dependency.]`

## fcm-telemetry-spawn

**No coupling.** Neither library imports the other. It is an FCM-coupled library and is not offered
for outside consumption, so co-installation is not a case a reader of this document reaches.

## fcm-xrpl

**No coupling.** Neither library imports the other. It is an FCM-coupled library and is not offered
for outside consumption, so co-installation is not a case a reader of this document reaches.
