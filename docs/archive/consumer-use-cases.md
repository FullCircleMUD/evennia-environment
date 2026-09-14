# Consumer use cases — brainstorm

**Not authoritative.** Working notes: what a consumer game actually wants to ask this library, written
down as they come up. Nothing here is agreed or designed. Keep entries short.

**None of these are things the library does.** They are things a consumer with that idea must be able
to build on top of it. The test is whether the library makes each one reachable, not whether it
ships it.

**Ruled out:** mob spawning. A different system is intended for it.

## UC-1 — movement cost

- Where: the movement mechanics — `at_pre_move`, or wherever the game prices a move.
- Asks: how much movement to deduct from this character for this room.
- From: terrain and weather together. The caller does not care which supplied what.

## UC-2 — hunger and thirst rate

- Where: the `evennia-survival` hooks — `at_pre_survival_tick`, `at_post_survival_tick`.
- Asks: does this tick apply, and how hard, given where the character is standing.
- Mostly weather, but terrain too: mountains dehydrate; a realm where time runs fast starves you.
  Terrain is not restricted to earthly terrain.
- Shape note: survival moves meters in **stages**, not amounts — the tick calls
  `increase_hunger()` / `increase_thirst()`, one stage, and `hunger_free_pass_tick` skips it. So
  "hungrier faster" is a stage count or a skipped tick, not a float.

## UC-3 — visibility, when rendering what a character can see

- Where: the look path — the `look` command, and whatever renders the room on entry, since arriving
  shows the same thing. Possibly a shared helper rather than the command.
- Asks: what can this character see from here.
- Mostly weather, sometimes terrain.
- Two distinct ranges, and they move independently: what is visible **in** the room — a whiteout
  hides the other people and objects standing in it — and what is visible **out** of it, into
  neighbouring rooms, which a moderate fog takes away while leaving the room itself readable.

## UC-4 — regeneration rate, and any other per-tick attribute change

- Where: the regeneration tick — `at_regeneration_tick` in `evennia-survival`. Far more frequent than
  the hunger and thirst tick: seconds rather than tens of minutes.
- Asks: what does standing here do to the rate things recover at.
- **Not only health.** Mana, or any attribute the game keeps. The consumer names it.
- **Can be negative.** Volcanic fields with sulphur in the air take health rather than adding it, so
  this is not a multiplier on a positive.
- Open: a stasis field where condition timers do not tick down at all — permanent haste while you
  stand in it. Unresolved whether that is a terrain or code on a specific room; raised as the kind of
  thing someone might want, not as a requirement.

## UC-5 — stealth and detection

- Asks: is hiding easier here, and is spotting someone harder.
- The same conditions as UC-3 read from the other side: fog hides as well as blinds.

## UC-6 — sound propagation

- Asks: does a shout carry to the neighbouring rooms, or does the storm drown it.
- The out-of-room half of UC-3, for hearing rather than sight.

## UC-7 — tracking

- Asks: can tracks be followed here, and for how long.
- Rain washes them out; rock never held them. Terrain and weather both.

## UC-8 — natural light

- Asks: is this room lit right now, given the terrain and the time of day.
- **Not indoor/outdoor — subject to natural light or not.** An underground terrain has none whatever
  the hour. An urban interior may have some, through windows. Every outdoor terrain has it.
- So terrain says whether daylight reaches here, and `evennia-calendar` says whether there is any.
  The calendar is already a hard dependency.
- Implies terrain types that are not landscapes: interiors and underground are terrains too.

## UC-9 — foraging and gathering

- Asks: can anything be foraged here, and what are the chances of finding it.
- Both halves: a gate, and a modifier on the odds.

## UC-10 — mob behaviour

- Asks: what do the creatures here do in these conditions.
- Shelter in a storm, hunt more in one, hibernate for a season. Season-driven as much as weather.

## UC-11 — exit passability

- Asks: is the pass snowed shut, is the ford in flood.
- A refusal rather than a cost, which makes it different in kind from UC-1.

## UC-12 — rest and camping

- Asks: can you rest here at all, and how well.
- Not in a blizzard; not in some terrains, ever. A gate on UC-4 rather than a rate.

## UC-13 — ambient messages

- Asks: what does this place say while you stand in it.
- The periodic "rain patters on the leaves", distinct from the static weather line a look prints.

## UC-14 — survivability

- Asks: is this room habitable without gear.
- Vacuum, deep water, extreme heat. A gate on being here at all.
