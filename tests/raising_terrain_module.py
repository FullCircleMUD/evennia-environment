# SPDX-License-Identifier: BSD-3-Clause
"""A consumer's declaration module that fails on import — CF-21, CF-22.

Stands in for any module the library cannot load: a typo in the consumer's own
code, a bad import, a name that does not exist yet. The setting itself is
perfectly well formed in both cases, which is the point — the refusal has to
carry the error underneath it or the consumer is told only that something
"could not be loaded".

It lives here rather than in ``tests.py`` because importing it raises, which is
the whole point.
"""

raise RuntimeError("deliberate failure on import — CF-21, CF-22")
