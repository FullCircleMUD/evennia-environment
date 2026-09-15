# Test plan

Every test case the library commits to covering, and the test function that covers it. The library is
built test-first: cases are agreed here, tests are written against them, then the implementation is
written to pass. The **Test function** column is the auditable trail — it is filled in as each test is
written, so an empty cell means the case is agreed but not yet covered.

Case IDs are stable and referenceable. Do not renumber; retire an ID rather than reuse it. Every test
function carries its case ID as its docstring, so the trail reads in both directions.

All test functions live in `src/evennia_environment/tests.py`.

Cases land here as each surface is agreed, and no code is written before they do. What is still being
designed is in [Open decisions](#open-decisions) below.

| Prefix | Covers |
|---|---|
| `SC` | The scaffold — the package installs and the runner runs |
| `EF` | `EnvironmentEffectType` — the shape a consumer declares one effect type in |
| `EE` | `EnvironmentEffect` — an effect type paired with a magnitude |
| `SH` | The stock helpers — `Constant`, `Multiply`, `Add`, `RoundUp`, `RoundDown`, `Chain` |
| `WT` | `WeatherType` — the shape a consumer declares one weather in |
| `WS` | `WeatherSlot` — one of a terrain's ten slots, day and night |
| `TT` | `TerrainType` — the shape a consumer declares one terrain in |
| `TP` | `TerrainProperty` — the attribute a room's terrain is held in |
| `RS` | `resolve()` — what a key answers, given a terrain and a weather |
| `RL` | What a refusal in play logs — the room's assignments and `resolve()` |
| `DR` | `refuse()` — the one route every declaration refusal takes, and what it logs |
| `CF` | The setting, and the boot check that refuses a bad one |
| `WB` | The weather band — one number a day, for the whole game |
| `DN` | Whether it is dark, held between watches |
| `RM` | `EnvironmentRoomMixin` — what a room answers about its surroundings |

## Fixtures

None. The `EF`, `EE`, `WT` and `TT` cases are pure Python — each takes its values and validates them
against each other, with no Evennia, no database and no room. The fixtures table grows when a surface
needs one.

The `TP` cases need two: a real Evennia typeclass carrying the property, since `AttributeProperty`
needs an attribute handler behind it, and two enums — the terrain one and an unrelated one, so TP-04
has something to be wrong against. Both follow `evennia-equipment`'s shape: typeclasses in
`tests/game_typeclasses.py`, enums in a module importing nothing but `enum`.

## SC — the scaffold

| ID | Case | Test function |
|---|---|---|
| SC-01 | The package imports and reports its version | `test_sc_01_package_imports_and_reports_its_version` |

## EF — `EnvironmentEffectType(key, return_type, default, requires)`

A frozen dataclass, and the only thing a consumer constructs to declare an effect type. It carries the
key's name, the type a helper must hand back, the helper that answers when nothing else does, and the
kwargs a call site has to supply.

**It validates itself in `__post_init__`, and it raises there rather than collecting.** A malformed
`EnvironmentEffectType(...)` is the consumer's own code failing at their own line, and a traceback
pointing at that line is worth more than a tidy list pointing at us. Boot-time collection applies to
the registry and the terrain tables, not to this.

**`return_type` describes what comes back from a helper, not what is declared here.** So it is checked
against an answer at the call, and all that can be checked at the declaration is that it is a usable
type.

**The default is a helper, like every other contribution.** A type whose sensible default is a
calculation — natural light, which is terrain and the hour together — would otherwise repeat that
calculation on every terrain that wanted it. `Constant(1.0)` is the static case.

### Construction

| ID | Case | Test function |
|---|---|---|
| EF-01 | A valid effect type carries its key, return type, default and requires unchanged | `test_ef_01_carries_its_key_return_type_default_and_requires` |
| EF-02 | The instance is frozen — assigning to a field after construction raises | `test_ef_02_is_frozen` |

### The key

| ID | Case | Test function |
|---|---|---|
| EF-03 | A key that is not a string is refused | `test_ef_03_refuses_a_key_that_is_not_a_string` |
| EF-04 | An empty key is refused — without a key the effect type names nothing | `test_ef_04_refuses_an_empty_key` |

### The return type

| ID | Case | Test function |
|---|---|---|
| EF-05 | A return type that is not a type object is refused — `"float"` names a type and is a string | `test_ef_05_refuses_a_return_type_that_is_not_a_type` |
| EF-13 | `typing.Any` is refused by name, and the refusal points at `object`. `isinstance(Any, type)` is `True`, so it passes the check above and then raises `TypeError` at the first answer — it would boot clean and crash in play | `test_ef_13_refuses_typing_any` |
| EF-14 | `object` is accepted, and is how a consumer declares that any answer will do. `isinstance(x, object)` is always `True`, so it needs no special case | `test_ef_14_accepts_object_as_the_anything_declaration` |

### The default helper

| ID | Case | Test function |
|---|---|---|
| EF-15 | A default that is not callable is refused — `1.0` names an answer but cannot be called for one | `test_ef_15_refuses_a_default_that_is_not_callable` |
| EF-16 | A default that cannot take the running value is refused — `lambda: 2.0` accepts nothing | `test_ef_16_refuses_a_default_that_cannot_take_the_running_value` |
| EF-17 | A default that cannot take the caller's kwargs is refused — `lambda value: 2.0` has nowhere to put them | `test_ef_17_refuses_a_default_that_cannot_take_the_kwargs` |

### What a call site must supply

| ID | Case | Test function |
|---|---|---|
| EF-18 | `requires` defaults to empty — a key needing nothing from the caller declares nothing | `test_ef_18_requires_defaults_to_empty` |
| EF-19 | A `requires` that is not a collection of strings is refused — these are kwarg names | `test_ef_19_refuses_a_requires_that_is_not_names` |

### The refusal

| ID | Case | Test function |
|---|---|---|
| EF-12 | Every refusal is a `ValueError` naming the key, so the consumer can find the declaration. One class for all of them — each one means "you declared this wrong", and one class is easier to catch | `test_ef_12_every_refusal_is_a_value_error_naming_the_key` |

## EE — `EnvironmentEffect(effect_type, helper)`

A frozen dataclass pairing a declared effect type with the helper that answers for it. This is what
terrain and weather carry: `EnvironmentEffectType` says `move_cost` is a float defaulting to
`Constant(1.0)`, and an `EnvironmentEffect` says what this swamp, or this blizzard, does about it.

```python
EnvironmentEffect(MOVE_COST, Constant(2.0))
```

**Declared means changed.** A terrain or weather only declares the keys it wants to be different from
the default. Silence is not an omission to be filled in — nothing runs, and the default's answer
stands.

**The helper is checked the same way the type's default is** — callable, takes the running value
positionally, takes `**kwargs`. Both go through one check, so a helper that would crash at the first
call is refused at the line that declared it.

**Nothing here looks at what the helper returns.** `return_type` is checked against an answer on the
call path, where it applies to every contribution rather than only to the one declared here.

**It carries no key of its own.** The key belongs to the type and is reached through it.

### Construction

| ID | Case | Test function |
|---|---|---|
| EE-01 | A valid effect carries its type and helper unchanged, and the type is the object that was passed | `test_ee_01_carries_its_type_and_helper` |
| EE-02 | The instance is frozen — assigning to a field after construction raises | `test_ee_02_is_frozen` |

### The effect type

| ID | Case | Test function |
|---|---|---|
| EE-03 | An effect type that is not an `EnvironmentEffectType` is refused — `"move_cost"` names one and is a string | `test_ee_03_refuses_a_type_that_is_not_an_effect_type` |

### The helper

| ID | Case | Test function |
|---|---|---|
| EE-09 | A helper that cannot be called as one is refused — not callable at all, or callable but unable to take the running value or the caller's kwargs. The rule itself is pinned by EF-15 to EF-17 against the default; this proves the same check is applied here | `test_ee_09_refuses_a_helper_that_cannot_be_called_as_one` |

### The refusal

| ID | Case | Test function |
|---|---|---|
| EE-08 | Every refusal is a `ValueError`. Where the type is a real `EnvironmentEffectType` the message names its key, so the consumer can find the declaration; where it is not, it names what was passed instead | `test_ee_08_every_refusal_is_a_value_error_naming_the_key` |

## SH — the stock helpers

Helpers a consumer will otherwise write for themselves, shipped so they do not have to. They are
tools, not a vocabulary: a consumer uses them, ignores them, or mixes them with their own functions,
and nothing here restricts what an effect may do.

```python
EnvironmentEffect(MOVE_COST, Constant(2.0))
EnvironmentEffect(MOVE_COST, Chain(Multiply(1.5), RoundUp()))
```

**Every one satisfies the helper contract** — `f(value, **kwargs) -> value` — so they go anywhere a
helper goes, including as a type's `default`. They are classes rather than closures so they carry a
readable `repr`, compare equal to their like, and validate their arguments at construction.

**They ignore `kwargs` and must still accept them**, because a call site passes the same kwargs to
every helper in the chain and one of them may want an actor the others do not.

**Not shipped:** subtract and divide, which are `Add` and `Multiply` with the number written
differently, and clamp, which nothing has asked for yet.

### Constant

| ID | Case | Test function |
|---|---|---|
| SH-01 | Returns its own value, ignoring what it was handed — this is what makes a declaration an override | `test_sh_01_returns_its_own_value_ignoring_what_came_before` |
| SH-02 | Carries a value of any type, not only numbers, so a key returning an enum member or a string can use it | `test_sh_02_carries_a_value_of_any_type` |

### Multiply and Add

| ID | Case | Test function |
|---|---|---|
| SH-03 | `Multiply` scales what it was handed | `test_sh_03_multiply_scales_what_it_was_handed` |
| SH-04 | `Multiply` refuses a factor that is not a number, at construction. A `bool` is refused too — `isinstance(True, int)` is `True`, so a plain numeric check would take it and scale by one | `test_sh_04_multiply_refuses_a_factor_that_is_not_a_number` |
| SH-05 | `Add` offsets what it was handed | `test_sh_05_add_offsets_what_it_was_handed` |
| SH-06 | `Add` refuses an amount that is not a number, on the same terms | `test_sh_06_add_refuses_an_amount_that_is_not_a_number` |

### RoundUp and RoundDown

An `int` effect type and a `Multiply` produce a float, which the return type refuses. These are how a
consumer lands back on a whole number.

| ID | Case | Test function |
|---|---|---|
| SH-07 | `RoundUp` returns an `int`, and goes up — including for a negative, where up means toward zero | `test_sh_07_round_up_goes_up_and_returns_an_int` |
| SH-08 | `RoundDown` returns an `int`, and goes down — including for a negative, where down means away from zero | `test_sh_08_round_down_goes_down_and_returns_an_int` |

### Chain

| ID | Case | Test function |
|---|---|---|
| SH-09 | Runs its helpers left to right, each handed what the one before it returned | `test_sh_09_runs_its_helpers_left_to_right` |
| SH-10 | Passes the caller's kwargs to every member, so a chain of three sees what one of them needs | `test_sh_10_passes_the_kwargs_to_every_member` |
| SH-11 | Refuses a member that cannot be called as a helper, at construction rather than part-way through a call | `test_sh_11_refuses_a_member_that_is_not_a_helper` |
| SH-12 | An empty chain returns what it was handed. It is the written form of "nothing happens here" | `test_sh_12_an_empty_chain_returns_what_it_was_handed` |

### The contract

| ID | Case | Test function |
|---|---|---|
| SH-13 | Every stock helper is accepted where a helper is required. They are classes with `__call__`, and the declaration check reads a signature — this pins that a bound `__call__` satisfies it, rather than assuming | `test_sh_13_every_stock_helper_satisfies_the_helper_contract` |

## WT — `WeatherType(key, effects, description, transition_in)`

A frozen dataclass, and the only thing a consumer constructs to declare one weather. It carries the
name the library looks it up by, the effects it declares, and two optional strings the consumer may
render.

```python
WeatherType(
    key="blizzard",
    effects=(
        EnvironmentEffect(MOVE_COST, Multiply(1.5)),
        EnvironmentEffect(VISIBILITY, Constant(0.2)),
    ),
    description="Snow drives across the ridge in sheets.",
)

WeatherType(key="sunny_with_some_clouds")   # declares nothing, changes nothing
```

**`effects` is a tuple of `EnvironmentEffect`, not a mapping.** Each entry carries its own type, so
the key lives in one place and a mapping's key cannot disagree with the entry filed under it. Stored
as a tuple whatever was passed, so a frozen weather is frozen in fact — a mutable collection here
would change every room using that weather, since effects resolve at read time.

**At most one effect per effect type.** A second entry for a type already declared is refused, naming
the key, identical or not. This is what guarantees the resolution chain is never longer than two, so
there is no ordering to configure and no merge rule to write.

**Declaring nothing is normal.** The mild end of a spectrum contributes nothing, and silence leaves
the default's answer standing. `effects` defaults to empty.

**An unregistered effect key is unrepresentable.** An `EnvironmentEffect` holds the type object
itself, so there is no way to name a key nobody declared — the check the earlier shape could not do
is now a thing that cannot be written.

**A query runs at most one of them.** The call names a key, so only the entry whose type matches is
consulted. A weather declaring five effects does not run five helpers.

**The two strings are opaque.** The library stores them and hands them back; it never renders them,
never decides when they are shown and never compares them. `description` is the weather line a
consumer puts under a room description. `transition_in` is what they render when this weather becomes
active — one per weather rather than a message per from-to pair, because an incoming message reads
correctly from any predecessor, and N strings beat N².

**Nothing constrains the key beyond being a non-empty string.** Spaces and punctuation are legal, as
they are for an effect key — the key is a mapping handle, and a player sees `description` and
`transition_in`.

### Construction

| ID | Case | Test function |
|---|---|---|
| WT-01 | A valid weather type carries its key, effects and both strings unchanged | `test_wt_01_carries_its_key_effects_and_both_strings` |
| WT-02 | The instance is frozen — assigning to a field after construction raises | `test_wt_02_is_frozen` |

### The key

| ID | Case | Test function |
|---|---|---|
| WT-03 | A key that is not a string is refused | `test_wt_03_refuses_a_key_that_is_not_a_string` |
| WT-04 | An empty key is refused — without a key the weather names nothing and no slot can hold it | `test_wt_04_refuses_an_empty_key` |

### The effects

| ID | Case | Test function |
|---|---|---|
| WT-05 | A weather declaring no effects is accepted, and `effects` defaults to empty — the mild end of a spectrum contributes nothing, which is an ordinary weather rather than a mistake | `test_wt_05_accepts_a_weather_declaring_no_effects` |
| WT-06 | Anything in `effects` that is not an `EnvironmentEffect` is refused, and so is an `effects` that cannot be iterated at all | `test_wt_06_refuses_effects_that_are_not_environment_effects` |
| WT-11 | A second effect for an effect type already declared is refused, naming the key | `test_wt_11_refuses_two_effects_for_one_effect_type` |
| WT-12 | Effects passed as a list are stored as a tuple, so what a weather holds cannot be mutated whatever the consumer handed over | `test_wt_12_stores_effects_as_a_tuple` |

### The optional strings

| ID | Case | Test function |
|---|---|---|
| WT-07 | Both strings default to `None` when the consumer declares neither | `test_wt_07_both_strings_default_to_none` |
| WT-08 | A description that is not a string is refused | `test_wt_08_refuses_a_description_that_is_not_a_string` |
| WT-09 | A transition_in that is not a string is refused | `test_wt_09_refuses_a_transition_in_that_is_not_a_string` |

### The refusal

| ID | Case | Test function |
|---|---|---|
| WT-10 | Every refusal is a `ValueError` naming the key, as every `EnvironmentEffectType` refusal is | `test_wt_10_every_refusal_is_a_value_error_naming_the_key` |

## WS — `WeatherSlot(day, night)`

One of a terrain's ten slots. It holds the weather that occurs there, and optionally a different one
for the dark watches.

```python
WeatherSlot(SCORCHING, night=FREEZING_CLEAR)   # a desert
WeatherSlot(BLIZZARD)                          # a blizzard is a blizzard
```

**`night` is filled with `day` at construction when it is not given.** Both are always populated, so
nothing downstream tests for absence — whatever resolves the active weather asks for one or the other
and gets a weather type either way. It also makes "does this slot differ at night" answerable as
`slot.night is slot.day`, with no flag to carry.

| ID | Case | Test function |
|---|---|---|
| WS-01 | A slot carries the day and night weather it was given, unchanged | `test_ws_01_carries_its_day_and_night` |
| WS-02 | Night not given is filled with the day weather, and is the same object | `test_ws_02_night_defaults_to_the_day_weather` |
| WS-03 | The instance is frozen — assigning to a field after construction raises | `test_ws_03_is_frozen` |
| WS-04 | A day that is not a `WeatherType` is refused | `test_ws_04_refuses_a_day_that_is_not_a_weather_type` |
| WS-05 | A night that is not a `WeatherType` is refused | `test_ws_05_refuses_a_night_that_is_not_a_weather_type` |

## TT — `TerrainType(key, effects, weather_slots, description)`

What a consumer declares one terrain as: its own effects, always in force, the ten weather slots
that can occur in it, and an optional description.

```python
scorch = WeatherSlot(SCORCHING, night=FREEZING_CLEAR)

TerrainType(
    key="desert",
    description="Dunes run to the horizon, and the air shimmers above them.",
    effects=(EnvironmentEffect(MOVE_COST, Constant(1.5)),),
    weather_slots={
        1: scorch, 2: scorch, 3: scorch, 4: scorch, 5: scorch,
        6: CLEAR, 7: CLEAR, 8: CLEAR, 9: SANDSTORM, 10: SANDSTORM,
    },
)
```

**Exactly ten slots, keyed 1 to 10.** Not nine, not eleven, no gaps. A terrain with no weather —
a cavern, an interior — declares ten of whatever its still air is called. Counting from one matches
`evennia-calendar`, which counts every position from one.

**The same weather in several slots is how a terrain weights it**, so the number of distinct weathers
is ten or fewer.

**Every slot value is a `WeatherSlot`. A `WeatherType` is not assignable to a terrain.** One shape,
no condition to explain: a slot that does not change after dark is `WeatherSlot(BLIZZARD)`, and
`WeatherSlot` fills its night from its day.

**Declared as a dict, stored as a tuple in slot order** — the same in-one-form, out-another as
`WeatherType.effects`, and for the same reason: a dict in a frozen dataclass is mutable, and mutating
it would change every room of that terrain at read time.

**Effects follow the same rule as a weather's** — a tuple of `EnvironmentEffect`, at most one per
effect type, through the shared check. A terrain declares only what it wants different from the
default.

### Construction

| ID | Case | Test function |
|---|---|---|
| TT-01 | A valid terrain carries its key, description, effects and ten slots unchanged | `test_tt_01_carries_its_key_description_effects_and_slots` |
| TT-02 | The instance is frozen — assigning to a field after construction raises | `test_tt_02_is_frozen` |

### The key

| ID | Case | Test function |
|---|---|---|
| TT-03 | A key that is not a string is refused | `test_tt_03_refuses_a_key_that_is_not_a_string` |
| TT-04 | An empty key is refused | `test_tt_04_refuses_an_empty_key` |

### The effects

| ID | Case | Test function |
|---|---|---|
| TT-05 | A terrain declaring no effects is accepted, and `effects` defaults to empty | `test_tt_05_accepts_a_terrain_declaring_no_effects` |
| TT-06 | The shared effects rule is applied here too — an entry that is not an `EnvironmentEffect` is refused, and so is a second effect for one effect type. The rule is pinned by the `WT` cases; this proves it runs for terrain as well | `test_tt_06_applies_the_shared_effects_rule` |

### The weather slots

| ID | Case | Test function |
|---|---|---|
| TT-07 | Slot keys must be exactly 1 to 10 — nine, eleven, a gap, a zero and a key that is not an integer are each refused, saying which slot is wrong | `test_tt_07_refuses_slot_keys_that_are_not_one_to_ten` |
| TT-09 | A slot value that is not a `WeatherSlot` is refused, a `WeatherType` included | `test_tt_09_refuses_a_slot_that_is_not_a_weather_slot` |
| TT-10 | Slots are stored as a tuple in slot order, so what a terrain holds cannot be mutated | `test_tt_10_stores_the_slots_as_a_tuple_in_slot_order` |

### The description

Opaque, like a weather's. The library stores it and hands it back; it never renders it and never
decides when it is shown.

| ID | Case | Test function |
|---|---|---|
| TT-12 | The description defaults to `None` when the consumer declares none | `test_tt_12_description_defaults_to_none` |
| TT-13 | A description that is not a string is refused | `test_tt_13_refuses_a_description_that_is_not_a_string` |

### The refusal

| ID | Case | Test function |
|---|---|---|
| TT-11 | Every refusal is a `ValueError` naming the key, so the consumer can find the declaration | `test_tt_11_every_refusal_is_a_value_error_naming_the_key` |

## TP — `TerrainProperty`

The `AttributeProperty` a room's terrain is held in. It validates that what is assigned is a member
of the game's terrain enum, which it reads from the setting through `config.terrain_enum()`:

```python
class Room(EnvironmentRoomMixin, DefaultRoom):
    pass            # the mixin brings terrain with it
```

Nothing is declared per typeclass. The enum arrives from `ENVIRONMENT_TERRAIN_ENUM`, resolved once
at boot and held for the process, so the property takes no arguments and the mixin can carry it.

**A string goes in the database; a member comes back out.** `at_set()` takes either the member or its
value and stores the value; `at_get()` resolves the value back to the member. So a consumer reads
`room.terrain is Terrain.MOUNTAINS`, while what is stored is `"mountains"` — a plain string that
nothing has to unpickle, that YAML can write, and that a builder command can type.

**That string form is what makes world content work.** Anything that builds a room in bulk carries
its terrain as text — a YAML field, a CSV column, a command argument — and none of them can hold an
enum member. Refusing strings would refuse every one of them.

**`strattr=True`.** The value is held in Evennia's string column, so "every room whose terrain is
swamp" is a database query rather than a walk. It is decided now because it cannot be added later: a
value written without the flag is invisible to a property declared with it.

**Terrain is write-once.** A room is given its terrain when it is built and does not change it in
play. Once a member is stored, a different one is refused; the same one passes and changes nothing,
so a build applying the same content twice is harmless. A builder that recreates its rooms never
meets the rule; one that tries to change a standing room's terrain is refused, which is the rule
working rather than a conflict with it.

**`None` is what an unassigned room holds, not a way to clear one.** Evennia's `autocreate` defaults
to `True`, so the first read of an unset attribute writes the default through `at_set()` — meaning
the default has to be acceptable. Once a terrain is stored, assigning `None` is refused like any
other change.

**A bad assignment is an `AttributeError`** — the descriptor protocol's own signal, and what
`evennia-equipment` raises from its `at_set()`. There is no declaration to get wrong here any more:
the enum comes from the setting, and a bad one is refused at boot as an `ImproperlyConfigured`.

**The property lives in `room.py` and is not re-exported from the package.** It imports Evennia, and
`__init__.py` runs while Django is still building its app registry. `evennia-equipment` exports
nothing from its package for the same reason. A consumer imports
`from evennia_environment.room import EnvironmentRoomMixin`.

**`at_set()` fires only on assignment through the property.** `room.db.terrain = "swamp"` writes past
it unvalidated. That is Evennia's behaviour and cannot be closed from here.

### Declaring the property

| ID | Case | Test function |
|---|---|---|
| TP-01 | A property declared with an enum reads as `None` on a room nothing has been assigned to | `test_tp_01_an_unassigned_room_has_no_terrain` |

### Assignment and storage

| ID | Case | Test function |
|---|---|---|
| TP-03 | A member of the declared enum is accepted, and reads back as that same member | `test_tp_03_accepts_a_member_and_reads_it_back` |
| TP-08 | The member's value as a string is accepted, and reads back as the member — the bulk-content path | `test_tp_08_accepts_the_members_value_as_a_string` |
| TP-10 | What is stored is the plain string, not the member. Read through the attribute handler rather than the property, since the property would resolve it and hide the difference | `test_tp_10_stores_the_plain_string` |
| TP-11 | `None` is accepted while nothing is stored, which is what an unassigned room holds | `test_tp_11_accepts_none_while_nothing_is_stored` |

### What is refused

| ID | Case | Test function |
|---|---|---|
| TP-04 | A member of a different enum is refused — this is the check the enum makes possible | `test_tp_04_refuses_a_member_of_a_different_enum` |
| TP-09 | A string matching no member's value is refused — `"swmap"` | `test_tp_09_refuses_a_string_matching_no_member` |
| TP-05 | A value that is neither a member nor a string is refused — a number, an object | `test_tp_05_refuses_a_value_that_is_neither_member_nor_string` |

### Write-once

| ID | Case | Test function |
|---|---|---|
| TP-12 | A different terrain assigned over a stored one is refused | `test_tp_12_refuses_a_different_terrain_over_a_stored_one` |
| TP-13 | The same terrain assigned again passes and changes nothing, so re-applying identical content is harmless | `test_tp_13_accepts_the_same_terrain_assigned_again` |
| TP-14 | `None` assigned over a stored terrain is refused — a terrain cannot be cleared | `test_tp_14_refuses_none_over_a_stored_terrain` |

### The refusal

| ID | Case | Test function |
|---|---|---|
| TP-07 | The refusal names what was assigned, so the mis-set is findable | `test_tp_07_the_refusal_names_what_was_assigned` |
| TP-15 | The refusal names the room, so a build applying content to hundreds of them says which one failed. `"terrain cannot be 'swmap'"` with no room is the bad value and no way to find it | `test_tp_15_the_refusal_names_the_room` |
| TP-16 | An unknown terrain name refuses without the enum's own `ValueError` chained underneath — the consumer's mistake is the name, not the lookup that went looking for it | `test_tp_16_an_unknown_name_does_not_chain_the_enums_own_error` |

## RS — `resolve(effect_type, terrain_type, weather_type, **kwargs)`

What a key answers. Given an effect type and whichever contributors apply, it runs them in order and
returns the value.

**Pure Python.** It takes the terrain and the weather as arguments rather than finding them, so it
needs no room, no database and no Evennia. The room accessor becomes a thin wrapper that finds both
and delegates. A consumer with a room-like thing that is not a room can call it directly.

**Both contributors are optional.** A room with no terrain, or one whose weather is not known yet,
still gets an answer — the default's.

```
value = effect_type.default(None, **kwargs)
if terrain declares this key:  value = terrain_helper(value, **kwargs)
if weather declares this key:  value = weather_helper(value, **kwargs)
```

**The return type is checked after every step, not once at the end**, so a refusal says which
contributor got it wrong rather than leaving three candidates. The default is checked too — a broken
default is as wrong as a broken contribution.

**The default is handed `None`**, nothing having run before it, so it produces the starting value
rather than passing one on. A helper written to return what it was given is a valid contribution and
an invalid default.

**Refusals are `ValueError`**, as every other refusal in this library is, with the message naming who
is at fault: the call site for a missing kwarg, the contributor for a bad return.

### Resolution

| ID | Case | Test function |
|---|---|---|
| RS-01 | With neither contributor, the default's answer comes back | `test_rs_01_with_neither_contributor_the_default_answers` |
| RS-02 | With only a terrain, its helper is handed the default's answer and its result is returned | `test_rs_02_a_terrain_is_handed_the_defaults_answer` |
| RS-03 | With only a weather, its helper is handed the default's answer | `test_rs_03_a_weather_is_handed_the_defaults_answer` |
| RS-04 | With both, terrain runs and then weather, each handed the running value. Proved with order-sensitive helpers, so a run in either order gives a different number | `test_rs_04_terrain_runs_then_weather` |
| RS-05 | A contributor that declares other keys but not this one changes nothing | `test_rs_05_a_contributor_declaring_other_keys_changes_nothing` |

### What the caller passes

| ID | Case | Test function |
|---|---|---|
| RS-06 | The caller's kwargs reach every helper, the default included | `test_rs_06_the_kwargs_reach_every_helper` |
| RS-07 | A missing required kwarg is refused, naming the key and which kwarg is absent | `test_rs_07_refuses_a_missing_required_kwarg` |
| RS-08 | Kwargs beyond what the key requires are passed through rather than refused, so a helper can use an optional one | `test_rs_08_passes_through_kwargs_beyond_what_is_required` |

### What a helper hands back

| ID | Case | Test function |
|---|---|---|
| RS-09 | A default returning something other than the declared return type is refused, and the refusal says it was the default | `test_rs_09_refuses_a_default_returning_the_wrong_type` |
| RS-10 | A terrain helper returning the wrong type is refused, and the refusal says it was the terrain | `test_rs_10_refuses_a_terrain_helper_returning_the_wrong_type` |
| RS-11 | A weather helper returning the wrong type is refused, and the refusal says it was the weather | `test_rs_11_refuses_a_weather_helper_returning_the_wrong_type` |

## RL — what a refusal in play logs

The refusals that can fire with a game up: the room's assignment refusals and `resolve()`'s. Unlike
the declaration and boot refusals, nobody is watching a console when these happen.

**The room's three go through `refuse_attribute()`**, the `AttributeError` sibling of `refuse()`.
`AttributeError` is the descriptor protocol's own signal and is what these already raise, so the only
behavioural change is the line on disk and the room's name in the message.

**`resolve()`'s two use `refuse()` unchanged** — they already raise `ValueError`, which is what it
raises. Nothing new is needed for them.

**Every occurrence is logged, and repeats are not suppressed.** `resolve()` is on the per-action path,
so one broken helper writes a line for every call that reaches it. That volume is the point: a log
filling with the same refusal is how a consumer finds out they have something to fix. Suppression
would be code carried for the life of the library to make a symptom quieter.

**The room refusals name the room.** A world build applies content to hundreds of rooms and the caller
may well catch per room and carry on, so a refusal that names only the bad value leaves an operator
with nothing to search for. `at_set()` has the object in hand; `_to_stored()` does not, and gets it
threaded through. The naming is pinned by TP-15 in both channels, since the exception wants it as much
as the log does.

**These fire with the game up, so the reactor is running** — evennia-logging-extension writes through
`log_file()` on a deferred rather than synchronously, which is the opposite of the window the `CF`
cases run in. The cases read the file back the same way regardless.

**`resolve()` documents itself as needing no room, no database and no Evennia.** That holds for the
answering path and no longer holds for the refusing one, which now reaches the log shim. A consumer
calling it from a bare script still gets the refusal; the line goes to `pre-startup.log`.

### The room's refusals

| ID | Case | Test function |
|---|---|---|
| RL-01 | `refuse_attribute()` logs its message to `environment.log` at ERROR, then raises `AttributeError` carrying it | `test_rl_01_logs_at_error_then_raises_an_attribute_error` |
| RL-02 | The log line and the exception carry the same text | `test_rl_02_the_log_line_and_the_exception_carry_the_same_text` |
| RL-03 | A refused write-once change lands a line naming the room | `test_rl_03_a_refused_write_once_change_lands_a_line` |
| RL-04 | A refused terrain name lands a line naming the room | `test_rl_04_a_refused_terrain_name_lands_a_line` |
| RL-05 | A refused value that is neither a member nor a string lands a line naming the room | `test_rl_05_a_refused_value_of_the_wrong_kind_lands_a_line` |
| RL-06 | An accepted assignment writes no log line | `test_rl_06_an_accepted_assignment_writes_no_log_line` |

### `resolve()`'s refusals

| ID | Case | Test function |
|---|---|---|
| RL-07 | A missing required kwarg lands a line, and still raises `ValueError` | `test_rl_07_a_missing_required_kwarg_lands_a_line` |
| RL-08 | A helper answering with the wrong type lands a line naming the contributor that got it wrong | `test_rl_08_a_wrong_type_lands_a_line_naming_the_contributor` |
| RL-09 | Two calls hitting the same problem land two lines — repeats are deliberately not suppressed, so a filling log is the signal that something needs fixing | `test_rl_09_the_same_problem_twice_lands_two_lines` |
| RL-10 | A resolve that answers writes no log line | `test_rl_10_a_resolve_that_answers_writes_no_log_line` |

## DR — `refuse()`, the one route a declaration refusal takes

Every refusal in `effects.py`, `terrain.py`, `weather.py` and `helpers.py` goes through one function
that logs the message at ERROR and then raises `ValueError` carrying it.

**It exists to make the logging provable.** A `raise ValueError` per site would need a delivery case
per site to be sure none was missed, and the next one added would slip through silently. One route
needs one delivery case, plus `DR-07` to hold the route closed.

**The exception type does not change.** They already raise `ValueError` — one class for "you declared
this wrong", easier to catch than a type per mistake — so `refuse()` raises that and the only
behavioural change is the line on disk.

**These fire as the consumer's declaration module imports**, which in a real boot is after Evennia has
set `DJANGO_SETTINGS_MODULE`, so `LOG_DIR` resolves and lines land in `environment.log`. A declaration
imported from a bare script or a REPL reaches `pre-startup.log` instead — an anomaly rather than a
boot phase, and evennia-logging-extension's business, not a case here.

`ERROR`, not `WARN`: a refused declaration means the consumer's game does not have the thing they
wrote down.

**The cases read the log back from disk**, for the reason the `CF` ones do — a mocked shim asserts a
call was made and passes while nothing lands in a file.

**`DR-03` to `DR-06` are one per module, not one per raise.** Each proves its module routes through
`refuse()` at all; `DR-07` is what covers the sites individually, by reading the source rather than by
exercising every one. A structural case because the risk is a site left behind, and no sampling of
call sites can see the one that was missed.

| ID | Case | Test function |
|---|---|---|
| DR-01 | `refuse()` logs its message to `environment.log` at ERROR, then raises `ValueError` carrying it | `test_dr_01_logs_at_error_then_raises_a_value_error` |
| DR-02 | The log line and the exception carry the same text | `test_dr_02_the_log_line_and_the_exception_carry_the_same_text` |
| DR-03 | A refused declaration in `effects.py` lands a line | `test_dr_03_a_refused_effect_declaration_lands_a_line` |
| DR-04 | A refused declaration in `terrain.py` lands a line | `test_dr_04_a_refused_terrain_declaration_lands_a_line` |
| DR-05 | A refused declaration in `weather.py` lands a line | `test_dr_05_a_refused_weather_declaration_lands_a_line` |
| DR-06 | A refused declaration in `helpers.py` lands a line | `test_dr_06_a_refused_helper_declaration_lands_a_line` |
| DR-07 | No `raise ValueError` remains in the four declaration modules outside `refuse()` itself — asserted over the parsed source, so a site added later is caught | `test_dr_07_no_declaration_module_raises_a_value_error_directly` |
| DR-08 | A declaration that is accepted writes no log line | `test_dr_08_an_accepted_declaration_writes_no_log_line` |

## CF — the setting and `check_settings()`

The consumer's terrain enum reaches the library as a setting naming it:

```python
ENVIRONMENT_TERRAIN_ENUM = "world.environment.Terrain"
ENVIRONMENT_TERRAIN_TYPES = "world.environment.TERRAINS"
ENVIRONMENT_DARK_WATCHES = (6, 1)
```

**Two settings, one file.** The enum names the terrains a game has; `TERRAINS` is the collection of
`TerrainType` carrying what each one does. They join on the string: `Terrain.SWAMP.value` is
`"swamp"`, which is the `TerrainType`'s key. No mapping to declare and none to keep in sync.

`config.py` holds the setting name, `check_settings()` and the accessor; `apps.py` calls the check
from `ready()`. Checking at boot rather than at first use is the point — validation deferred means a
misconfigured instance starts cleanly, runs, and then fails in front of a player.

**There is no terrain list the library could invent**, so the setting has no safe default. Without it
the instance does not start.

**Problems are collected, not reported one per restart.** A consumer with two things wrong gets both
in one refusal and fixes them in one pass. Where a check cannot run because an earlier one failed —
nothing to inspect if the module did not import — that is said rather than guessed at.

**An enum with no members is accepted.** It has a correct reading: someone booting to check their
install before writing content. What is refused is not declaring one at all.

**A third setting, naming the declaration module, lands when effect-type registration needs a known
moment to happen in.** Nothing does yet, and a setting with no consumer is a setting to get wrong.

**A refusal is logged before it is raised.** The console shows a traceback to whoever ran the start
command; `environment.log` is the durable record the consumer still has an hour later, and the one
they can be asked to send. Every refusal funnels through the single raise in `_refuse()` — the other
eleven are caught by `check_settings()` and folded into it — so one call site carries every reason
into the log without a delivery case per reason.

### The setting

| ID | Case | Test function |
|---|---|---|
| CF-01 | The setting absent is refused, and the refusal shows what a value looks like | `test_cf_01_refuses_an_absent_setting` |
| CF-02 | A setting that is empty or not a string is refused | `test_cf_02_refuses_a_setting_that_is_empty_or_not_a_string` |
| CF-03 | A path that cannot be imported is refused, and the original import error is chained rather than swallowed | `test_cf_03_refuses_a_path_that_cannot_be_imported` |
| CF-04 | A path naming something that is not an `Enum` class is refused | `test_cf_04_refuses_a_path_naming_something_that_is_not_an_enum` |

### The enum

| ID | Case | Test function |
|---|---|---|
| CF-05 | An enum with no members is accepted, alongside no terrain types — booting to check an install before writing content is a correct reading. An empty enum beside a populated table is a different thing, and CF-12 refuses it | `test_cf_05_accepts_an_enum_with_no_members` |
| CF-06 | Duplicate values are refused, naming the members Python folded. `JUNGLE = "forest"` silently becomes a second name for `FOREST`, leaving the game a terrain short with nothing raised | `test_cf_06_refuses_duplicate_values` |
| CF-07 | Values that are not strings are refused, naming them — a terrain's value is what a room stores and what YAML writes | `test_cf_07_refuses_values_that_are_not_strings` |

### The dark watches

Which of the calendar's six watches are dark. Numbers rather than names, because `PHASE_NAMES` are
documented as placeholders a game is expected to replace, so a name-based setting breaks when
someone renames them.

There is no safe default — the calendar deliberately refuses to say which watches are dark, so the
library cannot invent one either. Declaring an empty tuple is a game with no night, which is a
correct reading; not declaring at all is not.

| ID | Case | Test function |
|---|---|---|
| CF-15 | The dark-watches setting absent is refused | `test_cf_15_refuses_absent_dark_watches` |
| CF-16 | A setting that is not a collection of watch numbers is refused | `test_cf_16_refuses_dark_watches_that_are_not_watch_numbers` |
| CF-17 | A watch number outside 1 to 6 is refused, naming it — the calendar has six | `test_cf_17_refuses_a_watch_outside_one_to_six` |
| CF-18 | An empty tuple is accepted: a game with no night | `test_cf_18_accepts_no_dark_watches_at_all` |

### The terrain types

| ID | Case | Test function |
|---|---|---|
| CF-10 | The terrain-types setting absent is refused | `test_cf_10_refuses_an_absent_terrain_types_setting` |
| CF-11 | A path naming something that is not a collection of `TerrainType` is refused | `test_cf_11_refuses_terrain_types_that_are_not_terrain_types` |
| CF-12 | A terrain type whose key names no member of the enum is refused, naming it — it would be unreachable, since a room can only store a member's value | `test_cf_12_refuses_a_terrain_type_no_enum_member_names` |
| CF-13 | An enum member with no terrain type is accepted. Declaring the enum and filling in the terrains afterwards is how a game gets written | `test_cf_13_accepts_an_enum_member_with_no_terrain_type` |

### Collecting

| ID | Case | Test function |
|---|---|---|
| CF-08 | Two independent problems in one enum are reported together, in one refusal | `test_cf_08_reports_two_independent_problems_together` |
| CF-14 | A problem in each setting is reported together — the two are independent, so stopping at the first would cost a restart | `test_cf_14_reports_a_problem_in_each_setting_together` |

### Reading it back

| ID | Case | Test function |
|---|---|---|
| CF-09 | With a valid setting the accessor returns the consumer's enum, and `check_settings()` passes | `test_cf_09_a_valid_setting_resolves_to_the_enum` |

### Logging the refusal

The cases assert **delivery, not intent** — each reads the line back from the suite's `LOG_DIR`,
never by mocking `environment_log`. A mocked shim asserts only that a call was made; calendar's
CF-11 was written that way first and passed while no line ever reached disk. `check_settings()` runs
from `AppConfig.ready()` during `django.setup()`, before the reactor exists, and
evennia-logging-extension writes that window synchronously — which is what makes a boot refusal
logable at all.

`ERROR`, not `WARN`: the instance does not start.

**CF-20 is asserted against a configuration with two problems**, so same-text equality proves the
whole collected list reaches the log rather than just the first line of it. That is why there is no
separate "every problem is logged" case.

**CF-21 and CF-22 are separate because either setting can name a module that will not import**, and
each is checked by its own function. `could not be loaded` on its own tells a consumer what they
already knew from the traceback they could not keep, so the log carries the cause's full traceback
underneath the refusal — the line that broke is the part they can act on.

**The log gets more than the exception does.** A `raise ... from` takes one cause, so the exception
chains the first; the file has room for every broken module's traceback and gets all of them. That is
the one place the two channels deliberately differ, and CF-20's same-text assertion is `in` rather
than equality because of it.

`trace=True` will not supply the traceback. It formats the *active* exception, and `_refuse()` runs
after every `except` block has exited, so there is nothing active to format — the causes are carried
into the message explicitly.

| ID | Case | Test function |
|---|---|---|
| CF-19 | A refusal is logged to `environment.log` at ERROR before the raise, asserted by reading the file back | `test_cf_19_a_refusal_is_logged_to_disk_at_error` |
| CF-20 | The log line and the exception carry the same problem text, asserted where two problems were collected — the file and the console tell one story | `test_cf_20_the_log_line_and_the_exception_carry_the_same_text` |
| CF-21 | A terrain enum module that will not import logs the underlying error as well as the refusal | `test_cf_21_a_terrain_enum_that_will_not_import_logs_the_cause` |
| CF-22 | A terrain types module that will not import logs the underlying error as well as the refusal | `test_cf_22_terrain_types_that_will_not_import_log_the_cause` |
| CF-23 | A passing check writes no log line | `test_cf_23_a_passing_check_writes_no_log_line` |

## WB — the weather band

One number a day, one to ten, for the whole game. Every terrain reads the same band and answers with
its own weather, which is what makes neighbouring places correlated rather than independent — one
room is not snowing while the next is clear.

**Derived, never rolled.** `sha256(seed:day)` taken modulo six, then floored at three. Nothing is
stored in the database, no two processes have to agree on anything, and any day past or future can be
asked for.

**The hash gives three to eight; the season shifts it into the ten slots a terrain has.** Summer
moves it up two, winter down two, spring and autumn not at all:

| Season | Shift | Range |
|---|---|---|
| Winter | −2 | 1 – 6 |
| Spring, Autumn | 0 | 3 – 8 |
| Summer | +2 | 5 – 10 |

So slots 1 and 2 are reachable only in winter and 9 and 10 only in summer — a mountain snows in
winter and not in summer, and its clear summer day never happens in winter. The middle is reachable
in any season, which is what spring and autumn get. Whether slot 1 holds the good weather or the bad
is the consumer's; the library hands over a number.

**The season is required, not defaulted.** A band without one is not meaningful. `GameDate` carries
both the day and the season, so working one out costs a single call.

**Not Python's `hash()`.** It is randomised per process for strings, so two processes would disagree
about the weather; and it is the identity for small ints, so `hash(day) % 6` is a metronome rather
than weather.

**The seed is a setting with a safe default**, so it is not a boot check. Changing it rerolls a
world's entire weather history, and it is what stops two games on the same calendar having identical
skies.

Two surfaces: `weather_band(day, seed)` is the pure function; `current_weather_band()` is today's,
held between rollovers.

**Held, not recomputed.** Asking the calendar what day it is costs 3,600 ns against the hash's 514,
so the saving is not in caching the hash — it is in not asking at all. `day_changed` refreshes the
stored value, and a read only computes when there is nothing stored. One calculation, two triggers.

`[TBD — needs discussion: the roll happens at midnight, because that is when `day_changed` fires.
Putting it at dawn needs a declared dawn watch, and no setting names one. The same declaration the
day/night weather slots are waiting on.]`

### The band itself

| ID | Case | Test function |
|---|---|---|
| WB-01 | The band is an integer from 1 to 10 whatever the season, so it always names a slot a terrain has | `test_wb_01_the_band_is_one_to_ten` |
| WB-02 | The same day and seed always give the same band — derived rather than rolled, so no process has to agree with another | `test_wb_02_the_same_day_and_seed_always_give_the_same_band` |
| WB-03 | Consecutive days do not walk in step. Every band appears across a run of days, rather than the sawtooth `hash()` on an int would give | `test_wb_03_consecutive_days_do_not_walk_in_step` |
| WB-04 | A different seed gives a different band for the same day, so two games on one calendar do not share a sky | `test_wb_04_a_different_seed_gives_a_different_band` |

### The season's shift

| ID | Case | Test function |
|---|---|---|
| WB-08 | Winter shifts the band down two, landing in 1 to 6 — the only season that reaches slots 1 and 2 | `test_wb_08_winter_shifts_the_band_down` |
| WB-09 | Summer shifts it up two, landing in 5 to 10 — the only season that reaches slots 9 and 10 | `test_wb_09_summer_shifts_the_band_up` |
| WB-10 | Spring and autumn do not shift it, landing in 3 to 8, and give the same band as each other for a day | `test_wb_10_spring_and_autumn_do_not_shift_the_band` |

### The weather it names

The band is the slot number: both run 1 to 10, so a terrain's slots are indexed by it directly.

| ID | Case | Test function |
|---|---|---|
| WB-11 | `current_weather` returns the weather in the slot the band names | `test_wb_11_the_band_names_the_slot` |
| WB-12 | It returns the slot's night weather when it is dark and its day weather when it is not — which differ only where the slot declared a night | `test_wb_12_dark_reads_the_slots_night_weather` |

### Today's band

| ID | Case | Test function |
|---|---|---|
| WB-05 | A read with nothing held computes it — the lazy trigger, which is what answers between a restart and the next rollover | `test_wb_05_a_read_with_nothing_held_computes_it` |
| WB-06 | A second read returns what is held without recomputing | `test_wb_06_a_second_read_does_not_recompute` |
| WB-07 | `day_changed` refreshes what is held, so a rollover takes effect without anything asking the calendar | `test_wb_07_day_changed_refreshes_what_is_held` |

## DN — whether it is dark

Held between watches, the same shape as the band: `phase_changed` refreshes it, and a read computes
it when nothing is held — which is what answers between a restart and the next watch.

Nothing is stored in the database. Changing `ENVIRONMENT_DARK_WATCHES` and restarting is the whole
operation; there is no history to fix up.

| ID | Case | Test function |
|---|---|---|
| DN-01 | A watch the setting names is dark | `test_dn_01_a_declared_watch_is_dark` |
| DN-02 | A watch it does not name is light | `test_dn_02_a_watch_not_declared_is_light` |
| DN-03 | A read with nothing held works it out from the current watch | `test_dn_03_a_read_with_nothing_held_works_it_out` |
| DN-04 | A second read returns what is held without asking the calendar again | `test_dn_04_a_second_read_does_not_ask_the_calendar_again` |
| DN-05 | `phase_changed` refreshes what is held | `test_dn_05_phase_changed_refreshes_what_is_held` |

## RM — `EnvironmentRoomMixin`

What a room answers about its surroundings. Mixed into a consumer's own room typeclass, which
declares nothing — the mixin brings `terrain` with it, and the property reads the game's enum from
the setting.

```python
class Room(EnvironmentRoomMixin, DefaultRoom):
    pass
```

```python
cost = room.get_environment_effect(MOVE_COST, actor=character)
line = room.get_weather_description()
```

**Every method is a thin wrapper.** The room finds its terrain and its weather; `resolve()` does the
work. `get_environment_effect` passes both to it, and both being optional is what lets a room with no
terrain answer with the effect type's default rather than raising.

| ID | Case | Test function |
|---|---|---|
| RM-01 | `get_environment_effect` answers through this room's terrain and its active weather | `test_rm_01_answers_through_the_terrain_and_the_weather` |
| RM-02 | A room with no terrain still answers — the effect type's default | `test_rm_02_a_room_with_no_terrain_answers_the_default` |
| RM-03 | `get_terrain_description` returns this terrain's description, found by matching the stored member's value against the declared terrain types' keys | `test_rm_03_returns_the_terrains_description` |
| RM-04 | `get_terrain_description` on a room with no terrain returns `None` | `test_rm_04_a_room_with_no_terrain_has_no_description` |
| RM-08 | `get_terrain_description` on a terrain declaring no description returns `None` rather than raising | `test_rm_08_a_terrain_with_no_description_returns_none` |
| RM-05 | `get_weather_description` returns the active weather's description, working out the watch itself | `test_rm_05_returns_the_active_weathers_description` |
| RM-06 | `get_weather_description(day=False)` forces the night weather, overriding the watch | `test_rm_06_day_false_forces_the_night_weather` |
| RM-07 | A weather declaring no description returns `None` rather than raising | `test_rm_07_a_weather_with_no_description_returns_none` |
| RM-09 | `get_weather_description` on a room with no terrain returns `None` — there is no slot table to read a band against | `test_rm_09_a_room_with_no_terrain_has_no_weather` |

## The design

How the library is put together, and why, is in [design.md](design.md). This page is the cases.

## Open decisions

What has to be decided before the surface it belongs to can be built. Each is a question raised in
the design conversation and left open, not a gap to be filled by whoever reads this next.

**Terrain**
- `[TBD — needs discussion: whether every `Terrain` member must appear in the terrain table. Absent
  could mean "every effect at its default" or could mean the author forgot.]`
- `[TBD — needs discussion: whether a room with no terrain at all is legal and neutral, or a mistake
  worth refusing. Same question as the one above, from the room's side.]`
- `[TBD — needs discussion: the accessor. Whether the keyed form is the whole API, or whether an
  all-effects form exists alongside it for a builder or debug command, and what both are called.]`

**Weather**

- `[TBD — needs discussion: whether `WeatherType.effects` is stored as something immutable. Freezing
  the dataclass stops the attribute being rebound but not the mapping being mutated, and because
  effects resolve at read time, mutating it would change every room using that weather with nothing
  refusing it. WT-02 pins the frozen attribute, not the mapping's contents.]`
- `[TBD — needs discussion: whether an empty-string `description` or `transition_in` is refused. It
  has the same effect as `None` and probably means the author meant to write something, but refusing
  it is a rule nobody has asked for yet.]`
- `[TBD — needs discussion: how the active slot is chosen for a day. The ten slots are the candidate
  table and the draw is once per day; the function from day number and terrain to a slot is not
  designed. Note that weather keyed on `day_of_year` turns over at midnight, in the middle of the
  dark watches — a weather-day offset from the calendar day is what puts the roll at dawn, and it
  also decides whether a slot's night weather is the night after its day or the one before.]`
- `[TBD — needs discussion: how the dark-watches declaration is shaped and where it sits — a setting,
  or part of the consumer's declaration module alongside the terrains and effect keys.]`
- `[TBD — needs discussion: whether mountains are their own region or a terrain-driven index shift
  on a neighbouring one. The ten-slot structure has no region layer in it, so this may already be
  answered by terrain keying the slots — but that has not been said.]`
- `[TBD — needs discussion: whether exposure stays three tiers or becomes a scalar.]`

**The library**

- `[TBD — needs discussion: whether the library owns any tables. Nothing so far needs storing —
  terrain is declared and weather is derived from the day number — but this has not been ruled on.]`
**Where this came from.** The design conversation is summarised in the umbrella's
`ops/scratch/weather-library-exploration-2026-09-10.md`, which is a brainstorm and says so. Nothing
in it is agreed. Treat a shape lifted from it as an invention until it has been discussed here.

## Retired case IDs

Not reused. An ID names one behaviour for the life of the plan, so a commit or a docstring
referring to one always means the same thing.

`EF-06 — EF-11`, `ER-01 — ER-11`, `EE-04 — EE-06`, `EE-07`, `TT-08`, `TP-02`, `TP-06`

**The whole `ER` block, and the registry with it.** `EnvironmentEffectTypeRegistry` and
`ENVIRONMENT_EFFECT_TYPES` were read by nothing but their own cases. Every path in the library takes
the `EnvironmentEffectType` object — an effect holds one, `resolve()` is handed one, and
`_declared_by` matches on identity — so no key is ever looked up, and the master list had no reader.

The three jobs it would have done are done by the consumer keeping their declarations in one module,
which is what installing.md already tells them to do: that module is the master list, a terrain
referencing `MOVE_COST` gets a `NameError` on a typo before the library sees it, and the module itself
is what an enumerable vocabulary would be read from. FCM's own `catalogue.py` was written that way
without registering anything.
