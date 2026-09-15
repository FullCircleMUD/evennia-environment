# evennia-environment

Terrain and weather for Evennia — what a room's surroundings do to whoever is standing in it. A swamp
is slow, a blizzard is blinding, poison air hurts, and the game asks for each of those by name at the
call site that needs it.

## Status

**Feature complete, and untried against a real game.** A consumer declares their terrains, weathers
and effect types in one module, adds one mixin to their room typeclass, and every room answers. Every
case the suite covers is listed in
[docs/test-plan.md](https://github.com/FullCircleMUD/evennia-environment/blob/main/docs/test-plan.md).
See
[docs/installing.md](https://github.com/FullCircleMUD/evennia-environment/blob/main/docs/installing.md)
for what that looks like, and
[docs/progress.md](https://github.com/FullCircleMUD/evennia-environment/blob/main/docs/progress.md)
for where it is up to.

## The problem it solves

Most MUD weather is flavour: a line of prose when you enter a room, read by nothing. Making it bite
means every mechanic that cares — movement, visibility, survival, combat, spawning — reaching into a
weather system and knowing its vocabulary, and it means terrain doing the same thing separately.

Two systems that answer the same shape of question, wired into the same call sites twice.

## The approach

One library, one vocabulary, declared by the consumer.

The game declares the effect keys it will use, with a default for each. It declares its terrain types
and gives each one the values it overrides. Then any call site asks the room for the key it cares
about — `look` asks about visibility, movement asks about cost, the survival tick asks about health.
Weather contributes to the same keys, varying with the season and the day.

Any contribution can differ by day and night — a cavern is dark at noon, a pass costs more to cross
after dark, a desert freezes once the sun is down.

The library never invents a key and never applies one. It knows that keys exist, what they default to,
and how two contributors combine. What a value *means* is the game's business.

## Is this for you?

Probably, if you want terrain or weather in an Evennia game to do something mechanical rather than
print a line.

Probably not, if you want atmospheric weather messages and nothing else — that is a script and a
message table, and it does not need a library.

## Install

**What a game declares is in
[docs/installing.md](https://github.com/FullCircleMUD/evennia-environment/blob/main/docs/installing.md).**

Nothing is published yet. Editable install for development against a checkout:

```
git clone https://github.com/FullCircleMUD/evennia-environment.git
cd evennia-environment
python -m venv venv
# Activate the venv (platform-specific)
pip install evennia
pip install -e path/to/evennia-logging-extension  # sibling dependency, not on PyPI
pip install -e path/to/evennia-calendar           # sibling dependency, not on PyPI
pip install -e .
python runtests.py
```

## Learn more

- [docs/INDEX.md](https://github.com/FullCircleMUD/evennia-environment/blob/main/docs/INDEX.md) — the design wiki
- [docs/design.md](https://github.com/FullCircleMUD/evennia-environment/blob/main/docs/design.md) — how it is put together, and why.
- [docs/test-plan.md](https://github.com/FullCircleMUD/evennia-environment/blob/main/docs/test-plan.md) — every case the library commits to covering
- [docs/installing.md](https://github.com/FullCircleMUD/evennia-environment/blob/main/docs/installing.md) — everything a game declares
- [docs/interoperability.md](https://github.com/FullCircleMUD/evennia-environment/blob/main/docs/interoperability.md) — this library against its siblings
- [CLAUDE.md](https://github.com/FullCircleMUD/evennia-environment/blob/main/CLAUDE.md) — context for LLM agents working in this repo

## Licence

BSD 3-Clause. See [LICENSE](https://github.com/FullCircleMUD/evennia-environment/blob/main/LICENSE).
