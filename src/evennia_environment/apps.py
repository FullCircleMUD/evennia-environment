# SPDX-License-Identifier: BSD-3-Clause
"""The Django app, and the one thing it does at boot.

``ready()`` validates the consumer's configuration and nothing else. Checking
here rather than at first use is the point: validation deferred to the first
query means a misconfigured instance starts cleanly, runs, and then fails in
front of a player with a message about nothing in particular.
"""

from django.apps import AppConfig


class EnvironmentConfig(AppConfig):
    """Refuses the boot when the declared terrain enum is unusable."""

    name = "evennia_environment"
    label = "evennia_environment"
    verbose_name = "Evennia Environment"

    def ready(self):
        from evennia_calendar.signals import day_changed

        from evennia_environment.config import check_settings
        from evennia_environment.weather import refresh_weather_band

        check_settings()

        # Connections are module state and do not survive a reload, so this
        # runs wherever the app starts — which is once per process, and again
        # after a reload, since a reload restarts the process.
        day_changed.connect(refresh_weather_band, dispatch_uid="environment_band")
