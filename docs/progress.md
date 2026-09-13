# Progress

Running log of milestones with links to evidence. Reverse chronological — newest first.

## 2026-09-13 — repo scaffolded

The structure exists and nothing else. One smoke test (`SC-01`) proving the package imports and the
runner works; no library behaviour.

- Repo created and cloned into `libraries/evennia-environment/`, with `LICENSE` and `.gitignore`.
- The standard surfaces: `README.md`, `CLAUDE.md`, `docs/INDEX.md`, `docs/installing.md`,
  `docs/test-plan.md`, `docs/interoperability.md`, `docs/archive/`.
- `pyproject.toml` declaring Evennia, `evennia-logging-extension` and `evennia-calendar`.
- `log.py` binding `environment_log` to `environment.log`.
- `runtests.py`, `tests/test_settings.py` and `tests/urls.py`, adapted from `evennia-calendar`. The
  test settings install the calendar alongside this library.

No `config.py` and no `apps.py`. Both exist to check settings, and no setting is agreed yet.

**The design is not started.** [test-plan.md](test-plan.md) § Open decisions carries what has to be
settled before the first case can be written.
