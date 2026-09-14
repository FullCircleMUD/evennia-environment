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
| `EF` | `EnvironmentEffect` — the shape a consumer declares one effect in |
| `ER` | `EnvironmentEffectRegistry` — the master list, and registering against it |

## Fixtures

None. The `EF` cases are pure Python — `EnvironmentEffect` takes three values and validates them
against each other, with no Evennia, no database and no room. The fixtures table grows when a surface
needs one.

## SC — the scaffold

| ID | Case | Test function |
|---|---|---|
| SC-01 | The package imports and reports its version | `test_sc_01_package_imports_and_reports_its_version` |

## EF — `EnvironmentEffect(key, datatype, default)`

A frozen dataclass, and the only thing a consumer constructs to declare an effect. It carries the
key's name, the type its values are in, and the value a terrain gets when it declares nothing.

**It validates itself in `__post_init__`, and it raises there rather than collecting.** A malformed
`EnvironmentEffect(...)` is the consumer's own code failing at their own line, and a traceback
pointing at that line is worth more than a tidy list pointing at us. Boot-time collection applies to
the registry and the terrain tables, not to this.

### Construction

| ID | Case | Test function |
|---|---|---|
| EF-01 | A valid effect carries its key, datatype and default unchanged | `test_ef_01_carries_its_key_datatype_and_default` |
| EF-02 | The instance is frozen — assigning to a field after construction raises | `test_ef_02_is_frozen` |

### The key

| ID | Case | Test function |
|---|---|---|
| EF-03 | A key that is not a string is refused | `test_ef_03_refuses_a_key_that_is_not_a_string` |
| EF-04 | An empty key is refused — without a key the effect names nothing | `test_ef_04_refuses_an_empty_key` |

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

## ER — `EnvironmentEffectRegistry` and `register()`

The master list of effects. It lives in library code so the library owns its structure, and a consumer
adds to it from the module they declare their game in:

```python
from evennia_environment import ENVIRONMENT_EFFECTS, EnvironmentEffect

ENVIRONMENT_EFFECTS.register(EnvironmentEffect("movement_cost", float, 1.0))
```

**`ENVIRONMENT_EFFECTS` is an instance, not a module-level dict.** `EnvironmentEffectRegistry` is a
class and `ENVIRONMENT_EFFECTS` is the one the library exposes, so a test builds its own and no case
has to reset shared state between runs. ER-10 pins that the container is per-instance rather than a
mutable class attribute, which is where this design goes wrong if it goes wrong.

**Registration raises immediately**, like `EnvironmentEffect` itself, and for the same reason: the
call is in the consumer's own module, at a line they wrote. Boot-time collection belongs to
`check_settings()`, which is a separate piece of work — nothing here knows about settings, imports or
Django.

**The registry holds no values.** A key's datatype and its default are all it carries. The value for a
room comes from its terrain; the registry supplies the fallback when the terrain declares nothing for
that key, and the list a terrain's keys are validated against. Both of its jobs are served by
`get(key)`, which returns the `EnvironmentEffect` or `None`.

**`None` is a legitimate answer, not a failure.** Validating a terrain means asking about keys that
may not be registered — that is the question being asked — so a miss is an ordinary outcome and `get`
means what its name promises.

**This section covers `register()` and `get()` and nothing else.** Membership, iteration and listing
the master list each wait for a caller that wants them.

### Registering

| ID | Case | Test function |
|---|---|---|
| ER-01 | A registered effect can be looked up by its key, and is the object that was registered | `test_er_01_a_registered_effect_is_returned_by_its_key` |
| ER-02 | Registering something that is not an `EnvironmentEffect` is refused | `test_er_02_refuses_something_that_is_not_an_effect` |
| ER-03 | A fresh registry has nothing registered | `test_er_03_a_fresh_registry_has_nothing_registered` |
| ER-11 | `get()` on a key nobody registered returns `None` | `test_er_11_an_unregistered_key_returns_none` |

### The duplicate-key rule

An effect declared twice means one of the two declarations is being silently ignored, which is worth
refusing. Declaring the *same* effect twice is harmless — a module imported again, a consumer
re-running their declarations — so it passes and changes nothing.

| ID | Case | Test function |
|---|---|---|
| ER-04 | A second, different `EnvironmentEffect` under a key already registered is refused | `test_er_04_refuses_a_different_effect_under_a_taken_key` |
| ER-05 | Re-registering an identical `EnvironmentEffect` passes, and the key still resolves to that effect | `test_er_05_accepts_an_identical_effect_registered_twice` |
| ER-06 | The duplicate refusal is a `ValueError` naming the key, as every `EnvironmentEffect` refusal is | `test_er_06_the_duplicate_refusal_names_the_key` |

### Isolation

| ID | Case | Test function |
|---|---|---|
| ER-10 | Two registries do not share state — registering in one leaves the other empty | `test_er_10_two_registries_do_not_share_state` |

## Settled

What the design conversation has agreed, recorded so it is not reopened. Behaviour listed here still
needs cases before it is built.

- **The consumer declares three things in one module, and one setting names that module.** Their
  terrain types as an `Enum`, their effects registered against the library's master list, and the
  values each terrain gives for the effects it overrides.
- **`EnvironmentEffect` is the declared shape** — `key`, `datatype`, `default` — and the consumer
  constructs one per effect. Covered by the `EF` cases above.
- **The master list lives in library code, not the consumer's.** The consumer calls
  `ENVIRONMENT_EFFECTS.register(EnvironmentEffect(...))`; the library owns the container and its
  structure. The library imports the consumer's module itself, during `ready()`, so registration
  happens at a known moment.
- **A room stores its terrain as the `Enum` member**, validated in `at_set()`, which also accepts the
  member's string value so YAML-authored world content resolves at the assignment rather than later.
  Evennia's `dbserialize` round-trips an Enum member with identity intact.
- **Terrain effect values are absolute, not operations.** A swamp's movement cost is the number the
  author wrote. There is no merge algebra: terrain is the base value and weather modifies it, so the
  two are not symmetric contributors to one key.
- **Effects resolve at read time from the terrain, never cached on the room.** The room holds a
  reference; changing a terrain's numbers changes every room of that terrain with nothing to
  migrate. A per-room cache would go stale for as long as Evennia's idmapper holds the instance.

## Open decisions

What has to be settled before the surface it belongs to can be built. Each is a question raised in
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
- `[TBD — needs discussion: whether a terrain's effects vary by phase of day, as weather's do. The
  desert case that forced per-phase payloads for weather may or may not reach terrain.]`

**Weather**

- `[TBD — needs discussion: how per-phase payloads sit against the calendar's six watches. The
  exploration assumed four phases; the calendar shipped six, so either a terrain authors six payloads
  or the unwritten ones inherit.]`
- `[TBD — needs discussion: whether mountains are their own region or a terrain-driven index shift
  on a neighbouring one.]`
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
