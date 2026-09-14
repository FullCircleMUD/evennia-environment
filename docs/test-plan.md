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
| `WT` | `WeatherType` — the shape a consumer declares one weather in |
| `TT` | `TerrainType` — the shape a consumer declares one terrain in |
| `TP` | `TerrainProperty` — the attribute a room's terrain is held in |

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

## EF — `EnvironmentEffectType(key, datatype, default)`

A frozen dataclass, and the only thing a consumer constructs to declare an effect type. It carries the
key's name, the type its values are in, and the value a terrain gets when it declares nothing.

**It validates itself in `__post_init__`, and it raises there rather than collecting.** A malformed
`EnvironmentEffectType(...)` is the consumer's own code failing at their own line, and a traceback
pointing at that line is worth more than a tidy list pointing at us. Boot-time collection applies to
the registry and the terrain tables, not to this.

### Construction

| ID | Case | Test function |
|---|---|---|
| EF-01 | A valid effect type carries its key, datatype and default unchanged | `test_ef_01_carries_its_key_datatype_and_default` |
| EF-02 | The instance is frozen — assigning to a field after construction raises | `test_ef_02_is_frozen` |

### The key

| ID | Case | Test function |
|---|---|---|
| EF-03 | A key that is not a string is refused | `test_ef_03_refuses_a_key_that_is_not_a_string` |
| EF-04 | An empty key is refused — without a key the effect type names nothing | `test_ef_04_refuses_an_empty_key` |

### The datatype

| ID | Case | Test function |
|---|---|---|
| EF-05 | A datatype that is not a type object is refused — `"float"` names a type and is a string | `test_ef_05_refuses_a_datatype_that_is_not_a_type` |

### The default, against the datatype

**The check is `isinstance(default, datatype)` and nothing more.** The declared datatype is taken at
its word and the default has to be of it — no coercion, no widening. An author who declares `float`
writes `1.0`, not `1`, and the refusal says so at the line that got it wrong. `None` is the one
exemption.

| ID | Case | Test function |
|---|---|---|
| EF-06 | A default matching its datatype is accepted and stored unchanged | `test_ef_06_accepts_a_default_of_the_declared_type` |
| EF-07 | A default of an unrelated type is refused — `default="fast"` for a `float` | `test_ef_07_refuses_a_default_of_an_unrelated_type` |
| EF-08 | An int default for a `float` datatype is refused, not widened | `test_ef_08_refuses_an_int_default_for_a_float_datatype` |
| EF-09 | A float default for an `int` datatype is refused, not truncated | `test_ef_09_refuses_a_float_default_for_an_int_datatype` |
| EF-10 | A bool default for an `int` datatype is accepted. This is not a separate ruling — `isinstance(True, int)` is `True` in Python, so it follows from the rule above. Declaring `datatype=bool` is how a consumer means a boolean | `test_ef_10_accepts_a_bool_default_for_an_int_datatype` |
| EF-11 | A `None` default is accepted whatever the datatype, and exempt from the check. What `None` means is the consumer's, decided in the code that reads the value | `test_ef_11_accepts_a_none_default_whatever_the_datatype` |

### The refusal

| ID | Case | Test function |
|---|---|---|
| EF-12 | Every refusal is a `ValueError` naming the key, so the consumer can find the declaration. One class for all of them — each one means "you declared this wrong", and one class is easier to catch | `test_ef_12_every_refusal_is_a_value_error_naming_the_key` |

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

An effect type declared twice means one of the two declarations is being silently ignored, which
is worth refusing. Declaring the *same* effect type twice is harmless — a module imported again,
a consumer re-running their declarations — so it passes and changes nothing.

| ID | Case | Test function |
|---|---|---|
| ER-04 | A second, different `EnvironmentEffectType` under a key already registered is refused | `test_er_04_refuses_a_different_effect_type_under_a_taken_key` |
| ER-05 | Re-registering an identical `EnvironmentEffectType` passes, and the key still resolves to that effect type | `test_er_05_accepts_an_identical_effect_type_registered_twice` |
| ER-06 | The duplicate refusal is a `ValueError` naming the key, as every `EnvironmentEffectType` refusal is | `test_er_06_the_duplicate_refusal_names_the_key` |

### Isolation

| ID | Case | Test function |
|---|---|---|
| ER-10 | Two registries do not share state — registering in one leaves the other empty | `test_er_10_two_registries_do_not_share_state` |

## EE — `EnvironmentEffect(effect_type, magnitude)`

A frozen dataclass pairing a declared effect type with the value something gives for it. This is what
terrain and weather actually carry: `EnvironmentEffectType` says `movement_cost` is a float
defaulting to 1.0, and an `EnvironmentEffect` says this swamp, or this blizzard, makes it 2.5.

```python
EnvironmentEffect(MOVEMENT_COST, 2.5)
```

**The magnitude is checked against the type's own datatype** — the same `isinstance` rule, at the
same strictness the type applies to its default. No coercion, no widening, and a bool passing an
`int` datatype follows from the rule here exactly as it does in EF-10. The check reads the datatype
off the type it was handed, so nothing that *holds* these objects does any checking: not
`WeatherType`, not terrain.

**The check lives here rather than as a method on the type.** Terrain and weather both hold
`EnvironmentEffect` objects, so there is one call site, and a `validate()` on the type would be
indirection waiting for a second caller that does not exist.

**A `None` magnitude is refused, and that is not EF-11 being contradicted.** A type may default to
`None` because "no default" is a real state. "No magnitude" is not one: something that does not touch
visibility leaves visibility out of its collection, so omission already says it. A second way to say
nothing would have to be handled everywhere a value is read.

**It carries no key of its own.** The key belongs to the type and is reached through it. An accessor
that saves the hop waits for a caller that wants one.

### Construction

| ID | Case | Test function |
|---|---|---|
| EE-01 | A valid effect carries its type and magnitude unchanged, and the type is the object that was passed | `test_ee_01_carries_its_type_and_magnitude` |
| EE-02 | The instance is frozen — assigning to a field after construction raises | `test_ee_02_is_frozen` |

### The effect type

| ID | Case | Test function |
|---|---|---|
| EE-03 | An effect type that is not an `EnvironmentEffectType` is refused — `"movement_cost"` names one and is a string | `test_ee_03_refuses_a_type_that_is_not_an_effect_type` |

### The magnitude, against the type's datatype

| ID | Case | Test function |
|---|---|---|
| EE-04 | A magnitude of the type's declared datatype is accepted and stored unchanged | `test_ee_04_accepts_a_magnitude_of_the_declared_datatype` |
| EE-05 | A magnitude of an unrelated type is refused — `2.5` against a `str` effect type | `test_ee_05_refuses_a_magnitude_of_an_unrelated_type` |
| EE-06 | An int magnitude for a `float` effect type is refused, not widened. This is the rule most likely to be relaxed into a kindness later, so it is pinned | `test_ee_06_refuses_an_int_magnitude_for_a_float_type` |
| EE-07 | A `None` magnitude is refused, whatever the datatype | `test_ee_07_refuses_a_none_magnitude` |

### The refusal

| ID | Case | Test function |
|---|---|---|
| EE-08 | Every refusal is a `ValueError`. Where the type is a real `EnvironmentEffectType` the message names its key, so the consumer can find the declaration; where it is not, it names what was passed instead | `test_ee_08_every_refusal_is_a_value_error_naming_the_key` |

## WT — `WeatherType(key, effects, description, transition_in)`

A frozen dataclass, and the only thing a consumer constructs to declare one weather. It carries the
name the library looks it up by, what the weather contributes while it is active, and two optional
strings the consumer may render.

**It validates itself in `__post_init__` and raises there**, as `EnvironmentEffectType` does and
for the same reason: the declaration is a line in the consumer's own module, and the traceback
should point at it.

**Nothing constrains the key beyond being a non-empty string.** Spaces and punctuation are legal, as
they are for an effect key — the rule is the same on both, and a key with a space breaks nothing,
since it is a mapping handle. A player never sees it; they see `description` and `transition_in`.
Whether builder-facing surfaces make a spaced key awkward to type is a question for those surfaces
when they exist.

**It does not check its effect keys against the master list.** A weather may be declared before the
effects it names are registered — both happen in the consumer's own module, in whatever order they
wrote them — so refusing here would reject a declaration that is correct by the time the game boots.
That check belongs with boot validation, alongside the terrain tables.

**The two strings are opaque.** The library stores them and hands them back; it never renders them,
never decides when they are shown and never compares them. `description` is the weather line a
consumer puts under a room description. `transition_in` is what they render when this weather becomes
active — one per weather rather than a message per from-to pair, because an incoming message reads
correctly from any predecessor, and N strings beat N².

**The values inside `effects` are not covered here.** Whether a weather's value for a key overrides
terrain's or modifies it is open — see [Open decisions](#open-decisions) — and the answer decides
whether a value is a plain number or an operation. The cases below cover the mapping's presence and
shape, not what is in it.

### Construction

| ID | Case | Test function |
|---|---|---|
| WT-01 | A valid weather type carries its key, effects, description and transition_in unchanged | `test_wt_01_carries_its_key_effects_and_both_strings` |
| WT-02 | The instance is frozen — assigning to a field after construction raises | `test_wt_02_is_frozen` |

### The key

| ID | Case | Test function |
|---|---|---|
| WT-03 | A key that is not a string is refused | `test_wt_03_refuses_a_key_that_is_not_a_string` |
| WT-04 | An empty key is refused — without a key the weather names nothing and no slot can hold it | `test_wt_04_refuses_an_empty_key` |

### The effects mapping

| ID | Case | Test function |
|---|---|---|
| WT-05 | A weather declaring an empty effects mapping is accepted — the mild end of a spectrum contributes nothing, and that is an ordinary weather rather than a mistake | `test_wt_05_accepts_an_empty_effects_mapping` |
| WT-06 | An `effects` that is not a mapping is refused — a list of pairs is not one | `test_wt_06_refuses_effects_that_are_not_a_mapping` |

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

## TT — `TerrainType`

**A placeholder, deliberately.** It carries no fields yet. It exists so the room mixin can hold a
real class from the start and validate against it, rather than accepting a string now and being
retrofitted later when the fields are agreed.

What it will carry is in [Current thinking](#current-thinking) — the terrain's own environment
effects, always in force, and its ten numbered weather slots. None of that is designed, and no case
below anticipates it. Cases land here as each field is agreed, the same as everywhere else.

It is a frozen dataclass like the other declaration classes, decided now rather than later: adding a
field to a frozen class is nothing, while discovering a mutable one after rooms hold it is a change
to something already in use.

| ID | Case | Test function |
|---|---|---|
| TT-01 | A terrain type can be constructed, and is importable from the package | `test_tt_01_a_terrain_type_can_be_constructed` |
| TT-02 | The instance is frozen — assigning any attribute raises, before there is a field to assign to | `test_tt_02_is_frozen` |

## TP — `TerrainProperty`

The `AttributeProperty` a room's terrain is held in. It is declared with the consumer's terrain enum,
and validates that what is assigned to it is a member of that enum:

```python
class Room(DefaultRoom):
    terrain = TerrainProperty(Terrain)
```

The enum reaches the property at the declaration, the way `evennia-equipment`'s properties take their
slots and weights. Nothing here needs a setting, a registry or a declaration module.

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

**Two refusals, two exception types, split by who got it wrong.** A bad *assignment* is an
`AttributeError` — that is the descriptor protocol's own signal, and what `evennia-equipment` raises
from its `at_set()`. A bad *declaration*, TP-02, is a `ValueError`, like every other declaration in
this library, because it is a line in the consumer's class body rather than a value arriving at
runtime.

**The property lives in `room.py` and is not re-exported from the package.** It imports Evennia, and
`__init__.py` runs while Django is still building its app registry. `evennia-equipment` exports
nothing from its package for the same reason. A consumer imports
`from evennia_environment.room import TerrainProperty`.

**`at_set()` fires only on assignment through the property.** `room.db.terrain = "swamp"` writes past
it unvalidated. That is Evennia's behaviour and cannot be closed from here.

### Declaring the property

| ID | Case | Test function |
|---|---|---|
| TP-01 | A property declared with an enum reads as `None` on a room nothing has been assigned to | `test_tp_01_an_unassigned_room_has_no_terrain` |
| TP-02 | Declaring the property with something that is not an enum class is refused | `test_tp_02_refuses_a_declaration_that_is_not_an_enum` |

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
| TP-06 | Was "`None` is refused". Reversed by `autocreate=True` — the default is pushed through `at_set()` on first read, so refusing `None` makes an unassigned room unreadable. TP-11 and TP-14 carry the two halves of what replaced it |

## Current thinking

Where the design has got to. Everything here is the current working position and open to revision —
a later idea is not fighting a ruling. Behaviour listed here still needs cases before it is built.

### The effects vocabulary

- **The consumer declares three things in one module, and one setting names that module.** Their
  terrain types as an `Enum`, their effects registered against the library's master list, and the
  values each terrain gives for the effects it overrides.
- **`EnvironmentEffectType` is the declared shape** — `key`, `datatype`, `default` — and the consumer
  constructs one per effect type. Covered by the `EF` cases above.
- **A type declares a kind of effect; an `EnvironmentEffect` is one with a magnitude.** The type
  carries no value of its own, so the thing terrain and weather hold is the pairing. The same object
  serves both, and neither invents a payload format. Covered by the `EE` cases above.
- **The master list lives in library code, not the consumer's.** The consumer calls
  `ENVIRONMENT_EFFECT_TYPES.register(EnvironmentEffectType(...))`; the library owns the container
  and its structure. The library imports the consumer's module itself, during `ready()`, so
  registration happens at a known moment.
- **A room stores its terrain as the member's string value, and reads it back as the member.**
  `at_set()` takes either form and stores the string; `at_get()` resolves it. That is what lets
  YAML-authored world content assign a terrain, since a YAML file can only supply a string. Held as a
  `strattr` so it can be queried, and write-once, because a room is given its terrain when it is
  built and does not change it in play. Covered by the `TP` cases above.
- **Terrain effect values are absolute, not operations.** A swamp's movement cost is the number the
  author wrote. There is no merge algebra: terrain is the base value and weather modifies it, so the
  two are not symmetric contributors to one key.
- **Effects resolve at read time from the terrain, never cached on the room.** The room holds a
  reference; changing a terrain's numbers changes every room of that terrain with nothing to
  migrate. A per-room cache would go stale for as long as Evennia's idmapper holds the instance.

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

- `[TBD — needs discussion: whether a weather's value for a key it shares with terrain overrides the
  terrain's value or modifies it. Modify is the working lean — a blizzard ought to cost more in a
  swamp than on a road — and the answer decides whether a weather's payload is flat numbers like
  terrain's or carries operations. Nothing can be written for the weather registry until it is
  answered.]`
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
- `[TBD — needs discussion: whether the terrain tables are authored in YAML through
  `evennia-yaml-reader` as well as in Python. Registration is the substrate either way; a loader is
  additive and does not block the first cases.]`

**Where this came from.** The design conversation is summarised in the umbrella's
`ops/scratch/weather-library-exploration-2026-09-10.md`, which is a brainstorm and says so. Nothing
in it is agreed. Treat a shape lifted from it as an invention until it has been discussed here.
