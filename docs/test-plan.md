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
| `ER` | `EnvironmentEffectTypeRegistry` — the master list, and registering against it |
| `EE` | `EnvironmentEffect` — an effect type paired with a magnitude |
| `SH` | The stock helpers — `Constant`, `Multiply`, `Add`, `RoundUp`, `RoundDown`, `Chain` |
| `WT` | `WeatherType` — the shape a consumer declares one weather in |
| `WS` | `WeatherSlot` — one of a terrain's ten slots, day and night |
| `TT` | `TerrainType` — the shape a consumer declares one terrain in |
| `TP` | `TerrainProperty` — the attribute a room's terrain is held in |
| `RS` | `resolve()` — what a key answers, given a terrain and a weather |
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

### Retired

| ID | Why |
|---|---|
| EF-06 — EF-11 | All six checked a default *value* against the declared datatype. The default is a helper now, so there is no value at the declaration to check. The type check they were doing moves to the call path, where it applies to every answer rather than only to the default |

## ER — `EnvironmentEffectTypeRegistry` and `register()`

The master list of effect types. It lives in library code so the library owns its structure, and
a consumer adds to it from the module they declare their game in:

```python
from evennia_environment import ENVIRONMENT_EFFECT_TYPES, EnvironmentEffectType

ENVIRONMENT_EFFECT_TYPES.register(EnvironmentEffectType("movement_cost", float, 1.0))
```

**`ENVIRONMENT_EFFECT_TYPES` is an instance, not a module-level dict.**
`EnvironmentEffectTypeRegistry` is a class and `ENVIRONMENT_EFFECT_TYPES` is the one the library
exposes, so a test builds its own and no case has to reset shared state between runs. ER-10 pins
that the container is per-instance rather than a mutable class attribute, which is where this
design goes wrong if it goes wrong.

**Registration raises immediately**, like `EnvironmentEffectType` itself, and for the same reason: the
call is in the consumer's own module, at a line they wrote. Boot-time collection belongs to
`check_settings()`, which is a separate piece of work — nothing here knows about settings, imports or
Django.

**The registry holds no values.** A key's datatype and its default are all it carries. The value for a
room comes from its terrain; the registry supplies the fallback when the terrain declares nothing for
that key, and the list a terrain's keys are validated against. Both of its jobs are served by
`get(key)`, which returns the `EnvironmentEffectType` or `None`.

**`None` is a legitimate answer, not a failure.** Validating a terrain means asking about keys that
may not be registered — that is the question being asked — so a miss is an ordinary outcome and `get`
means what its name promises.

**This section covers `register()` and `get()` and nothing else.** Membership, iteration and listing
the master list each wait for a caller that wants them.

### Registering

| ID | Case | Test function |
|---|---|---|
| ER-01 | A registered effect type can be looked up by its key, and is the object that was registered | `test_er_01_a_registered_effect_type_is_returned_by_its_key` |
| ER-02 | Registering something that is not an `EnvironmentEffectType` is refused | `test_er_02_refuses_something_that_is_not_an_effect_type` |
| ER-03 | A fresh registry has nothing registered | `test_er_03_a_fresh_registry_has_nothing_registered` |
| ER-11 | `get()` on a key nobody registered returns `None` | `test_er_11_an_unregistered_key_returns_none` |

### The duplicate-key rule

**The key is the identity.** Two declarations under one key are the same effect type as far as the
library can tell, and one of them is being ignored — so the second is refused, whatever it holds.

Comparing the declarations instead is no longer possible. A default is a helper, and two
separately-written declarations hold different function objects even when they read identically, so
"is this the same declaration" has no answer the library can trust.

| ID | Case | Test function |
|---|---|---|
| ER-04 | A second effect type under a key already registered is refused, whatever it declares | `test_er_04_refuses_a_second_effect_type_under_a_taken_key` |
| ER-06 | The duplicate refusal is a `ValueError` naming the key, as every declaration refusal is | `test_er_06_the_duplicate_refusal_names_the_key` |

### Retired

| ID | Why |
|---|---|
| ER-05 | Was "re-registering an identical effect type passes". Two separately-built declarations can no longer be identical — their helpers are different function objects — so the case tested something that cannot happen. ER-04 now covers every second registration |

### Isolation

| ID | Case | Test function |
|---|---|---|
| ER-10 | Two registries do not share state — registering in one leaves the other empty | `test_er_10_two_registries_do_not_share_state` |

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

### Retired

| ID | Why |
|---|---|
| EE-04 — EE-06 | All three checked a magnitude against the type's datatype. There is no magnitude now — a contribution is a helper, and what it returns is checked where it is called |
| EE-07 | Was "a `None` magnitude is refused". Absorbed into EE-09: `None` is not callable, so it fails the helper check like anything else that cannot answer |

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

### Retired

| ID | Why |
|---|---|
| TT-08 | Was "a bare `WeatherType` as a slot value is wrapped into a `WeatherSlot`". One shape is worth more than the four characters wrapping saved: a consumer choosing between two classes on a condition is a rule to document and to get wrong |

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

**That string form is what makes world content work.** `evennia-world-builder` applies attributes
with `setattr` after `create_object`, so assignment runs through this property — and a YAML file can
only supply a string. Refusing strings would fail every world-built room.

**`strattr=True`.** The value is held in Evennia's string column, so "every room whose terrain is
swamp" is a database query rather than a walk. It is decided now because it cannot be added later: a
value written without the flag is invisible to a property declared with it.

**Terrain is write-once.** A room is given its terrain when it is built and does not change it in
play. Once a member is stored, a different one is refused; the same one passes and changes nothing,
so a build applying the same content twice is harmless. `evennia-world-builder` tears down and
recreates rather than updating in place, so a rebuild assigns each room exactly once.

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
| TP-08 | The member's value as a string is accepted, and reads back as the member — the world-builder path | `test_tp_08_accepts_the_members_value_as_a_string` |
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

### Retired

| ID | Why |
|---|---|
| TP-02 | Was "declaring the property with something that is not an enum class is refused". There is nothing to declare it with now — the enum comes from the setting, so that check is CF-04, made once at boot rather than per typeclass |
| TP-06 | Was "`None` is refused". Reversed by `autocreate=True` — the default is pushed through `at_set()` on first read, so refusing `None` makes an unassigned room unreadable. TP-11 and TP-14 carry the two halves of what replaced it |

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

## Current thinking

Where the design has got to. Everything here is the current working position and open to revision —
a later idea is not fighting a ruling. Behaviour listed here still needs cases before it is built.

### The effects vocabulary

- **The consumer declares three things in one module, and one setting names that module.** Their
  terrain types as an `Enum`, their effects registered against the library's master list, and the
  values each terrain gives for the effects it overrides.
- **`EnvironmentEffectType` is the declared shape** — `key`, `datatype`, `default` — and the consumer
  constructs one per effect type. Covered by the `EF` cases above.
- **A type declares a kind of effect; an `EnvironmentEffect` pairs one with a helper.** The type
  carries no answer of its own, so the thing terrain and weather hold is the pairing. The same object
  serves both, and neither invents a payload format.
- **The master list lives in library code, not the consumer's.** The consumer calls
  `ENVIRONMENT_EFFECT_TYPES.register(EnvironmentEffectType(...))`; the library owns the container
  and its structure. The library imports the consumer's module itself, during `ready()`, so
  registration happens at a known moment.
- **A room stores its terrain as the member's string value, and reads it back as the member.**
  `at_set()` takes either form and stores the string; `at_get()` resolves it. That is what lets
  YAML-authored world content assign a terrain, since a YAML file can only supply a string. Held as a
  `strattr` so it can be queried, and write-once, because a room is given its terrain when it is
  built and does not change it in play. Covered by the `TP` cases above.
- **Effects resolve at read time from the terrain, never cached on the room.** The room holds a
  reference; changing a terrain's numbers changes every room of that terrain with nothing to
  migrate. A per-room cache would go stale for as long as Evennia's idmapper holds the instance.

### Asking a room, and how an answer is resolved

- **A call site asks for one key at a time, and gets a value back.** The library returns; it never
  reaches out and changes anything. Everything in
  [archive/consumer-use-cases.md](archive/consumer-use-cases.md) is reachable that way — a hook that
  was already running asks a question and decides locally.
- **An effect carries a helper, not a value.** `f(value, **kwargs) -> value`. A static answer is a
  stock helper — `Constant(2.0)` — so there is one shape and one code path, and a value that depends
  on the hour or on who is asking is the same shape as one that does not.
- **The caller's kwargs pass straight through** to every helper, including the character and anything
  else a key needs. The library does not inspect them.
- **Helpers read; they do not mutate.** A consumer's helper is their code and can do what they write,
  but the library's contract is the returned value, and a helper that changes things makes a query
  unsafe — movement prices a destination nobody is standing in.
- **At most one effect per key per contributor.** A terrain declares one effect for `move_cost`; so
  does a weather. A second for a key already present is refused at the declaration, naming the key,
  identical or not — two entries in one literal is a paste error, not a module loaded twice.
- **Resolution is the default, then terrain, then weather.** Fixed, documented, not configurable.
  Each receives the running value; nothing declared for that key leaves it untouched.

```python
value = default_helper(None, **kwargs)
if terrain declares this key:  value = terrain_helper(value, **kwargs)
if weather declares this key:  value = weather_helper(value, **kwargs)
```

- **That is the whole combination rule.** No kinds, no priorities, no tiebreaks, no merge algebra.
  One-per-contributor is what buys it: the chain is never longer than two, so there is no ordering
  problem to solve. Whether a contribution replaces or modifies is the helper's own choice —
  `Constant` ignores what it was handed, anything else uses it.
- **The default is a helper too, and is the starting value.** A type whose sensible default is a
  calculation — natural light, which is terrain and the hour together — would otherwise repeat that
  calculation on every terrain that wanted it.
- **The cost, taken deliberately: terrain cannot react to weather.** A vale that amplifies whatever
  the sky is doing is not writable as a terrain effect, since terrain runs first. A weather helper can
  look at the room's terrain and do it from that side. Nothing in the use cases wants it.
- **Terrain tables are Python, not YAML.** A YAML file cannot hold a function. This does not touch
  world content — a room still gets `terrain: swamp` from YAML, because that is a string naming a
  member.

### Weather and the terrain's weather slots

- **Weather types are registered the way effects are.** `blizzard`, `thunderstorm`, `scorching_hot` —
  one entry each, declared once and referenced from any terrain that can have it. The names are the
  consumer's, as the effect keys are.
- **A weather type carries environment effects**, against keys the consumer has already registered. A
  weather with no effects at all is legal and expected: the mild end of a spectrum — sunny with some
  clouds — contributes nothing.
- **It also carries two optional strings the consumer renders and the library never touches** — a
  description for the weather line under a room description, and a transition rendered when this
  weather becomes active. One incoming message per weather, not a message per from-to pair. Covered
  by the `WT` cases above.
- **A terrain carries its own environment effects too**, always in force and independent of the
  weather. Crossing a swamp costs more whatever the sky is doing.
- **A terrain has exactly ten numbered weather slots, every one filled.** Not "up to ten". The same
  weather may occupy several slots, which is how a terrain weights it, so the number of *distinct*
  weathers is ten or fewer.
- **Each slot holds a day weather and an optional night weather.** Left empty, the day weather stands
  through the dark — a blizzard at night is still a blizzard. Filled, a different registry entry takes
  over during the dark watches, which is how a desert is scorching by day and freezing by night under
  the same clear sky. The night entry is another weather with its own effects, not an inverse of the
  day one.
- **The variance belongs to the terrain, not to the weather type.** A clear sky is not inherently
  freezing at night; it is freezing at night *in a desert*. Putting the day/night pair on the weather
  type instead would need a separate entry per terrain and lose the reuse the registry exists for.
- **The consumer declares which of the six watches are dark.** `evennia-calendar` reports the watch
  and deliberately does not say which are night — "which of them are dark is the game's business, not
  ours" — so the mapping is declared alongside the terrains and the effect keys.
- **One weather draw per day**, the dusk swap being the only change within it. That is what keeps the
  active weather a pure function of the day number, the terrain and a seed: nothing stored, nothing
  to migrate, and every process in a multi-instance deployment computing the same answer without
  coordinating. Drawing per watch would need stored state and would make the night slot meaningless.
- **A room always has a weather.** Every slot is filled, so there is no null state and the library
  never models an absence of weather.
- **What a character gets is the terrain's effects and the active weather's, together.** Different
  consumer systems read different keys out of that set, at whatever moment each of them runs.

## Open decisions

What has to be decided before the surface it belongs to can be built. Each is a question raised in
the design conversation and left open, not a gap to be filled by whoever reads this next.

**The effects registry**

- `[TBD — needs discussion: the rest of the read surface. Looking a key up is all `register()` needs
  to be testable; membership, iteration, listing the master list and what a key nobody registered
  does are each waiting for a caller that wants them.]`
- `[TBD — needs discussion: whether registration closes once boot validation has run. A key
  registered afterwards would not have been checked against terrains already validated against the
  list. Belongs with `check_settings()`, which is where boot is a thing that has happened.]`

**Terrain**

- `[TBD — needs discussion: whether the terrain-to-effects table is registered the way effects are —
  `TERRAINS.register(Terrain.SWAMP, {...})` — or stays a consumer-authored dict validated at boot.
  Registration would validate each terrain against the master list at the line that declared it,
  which is the argument that carried for effects.]`
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
