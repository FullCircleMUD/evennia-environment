# SPDX-License-Identifier: BSD-3-Clause
"""The one route a declaration refusal takes.

Every refusal in ``effects.py``, ``terrain.py``, ``weather.py`` and
``helpers.py`` comes through here. One route rather than a raise at each site is
what makes the logging provable: a delivery case covers all of them, and DR-07
holds the route closed against the next one added.

The boot check has its own refusal in ``config.py`` — a different exception, a
collected list of problems, and a chained cause under it. This is the one for a
single declaration the consumer wrote wrong.

See docs/test-plan.md § DR.
"""


def refuse(message):
    """Log ``message`` at ERROR, then raise it as a ``ValueError``.

    ``ValueError`` because that is what every declaration already raised: one
    class for "you declared this wrong" is easier to catch than a type per
    mistake.

    The raise happening here rather than at the call site puts one more frame
    on the traceback. The consumer's own line is still on it, one above, which
    is the frame they were going to read.
    """
    # Inside the function, as config.py does: these modules are imported while
    # Django is still building its app registry, and the library standards hold
    # log imports out of module scope.
    from evennia_environment.log import environment_log

    # ERROR rather than WARN — the consumer's game does not have the thing
    # they wrote down.
    environment_log(message, level="ERROR")

    raise ValueError(message)


def refuse_attribute(message, suppress_context=False):
    """Log ``message`` at ERROR, then raise it as an ``AttributeError``.

    ``AttributeError`` is the descriptor protocol's own signal and what a
    refused assignment already raised.

    ``suppress_context`` is for a refusal raised from inside an ``except``
    block whose exception is machinery rather than diagnosis — the enum lookup
    that went looking for a terrain name is not what the consumer got wrong.

    See docs/test-plan.md § RL.
    """
    from evennia_environment.log import environment_log

    environment_log(message, level="ERROR")

    if suppress_context:
        raise AttributeError(message) from None

    raise AttributeError(message)
