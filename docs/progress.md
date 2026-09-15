# Progress

Running log of milestones with links to evidence. Reverse chronological — newest first.

## 2026-09-15 — every refusal logs

Every refusal in the library writes to `environment.log` at ERROR before raising — the boot check, the
declarations, the room's assignments and `resolve()`. Why it is built that way is in
[design.md](design.md) § Everything that raises, logs.

- `refusal.py` added, holding the routes a declaration and an assignment take.
- Boot refusals, room refusals and resolve refusals all verified landing on disk, read back from the
  file rather than through a mocked shim.

**Not tried against a real game**, so no refusal here has been read by a consumer troubleshooting one.

## 2026-09-14 — feature complete

A game can declare its terrains, weathers and effect types, mix one class into its room typeclass,
and ask any room what its surroundings do.

- Declarations: `EnvironmentEffectType`, `EnvironmentEffect`, `WeatherType`, `WeatherSlot`,
  `TerrainType`.
- Stock helpers: `Constant`, `Multiply`, `Add`, `RoundUp`, `RoundDown`, `Chain`.
- `resolve()` — the default, then the terrain, then the weather, each handed the running value.
- `EnvironmentRoomMixin` — `get_environment_effect`, `get_terrain_description`,
  `get_weather_description`, and the `terrain` property.
- Three required settings, one optional, checked at boot by `apps.ready()`.
- Weather derived from the calendar: a band a day, shifted by season, held between signals.

136 tests via `python runtests.py`. Every case in [test-plan.md](test-plan.md) has a test and every
test traces to a case.

**Not tried against a real game.** No consumer has installed it.
