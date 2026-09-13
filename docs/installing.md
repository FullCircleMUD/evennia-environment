# Installing

What a game has to do to run this library. Written as each requirement is decided rather than
reconstructed afterwards, so it describes what exists.

**The library is scaffolded and does nothing yet**, so the list below stops after the app is
installed. The steps that declare terrain, register effect keys and start weather land as each is
agreed in [test-plan.md](test-plan.md).

## 1. Install the package

Nothing is published yet, so install from a checkout — and both sibling dependencies are also
unpublished, so they install from their own checkouts first:

```
pip install -e path/to/evennia-logging-extension
pip install -e path/to/evennia-calendar
pip install -e path/to/evennia-environment
```

## 2. Add the app

In your settings:

```python
INSTALLED_APPS += ["evennia_calendar", "evennia_environment"]
```

`evennia-calendar` is a hard dependency — weather reads the season and the phase of day from it — so
it is installed and configured alongside. What the calendar itself needs is in
[its own installing.md](../../evennia-calendar/docs/installing.md).

## Required settings

None yet. The library reads no settings, because it does nothing yet.

## Optional settings

None yet.

## What is not checked for you

- **That the library is in `INSTALLED_APPS`.** Leave it out and `AppConfig.ready()` never runs, so
  nothing validates anything. There is nothing to validate today, so nothing is lost — but the same
  omission will silently skip every check added from here.
- **That a library import in your settings file sits below `from evennia.settings_default import *`.**
  `LOG_DIR` is set by that import, and a library imported above it is refused at boot. Where your game
  overrides `LOG_DIR`, the override goes directly under that import.
