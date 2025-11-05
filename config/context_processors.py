"""Project-level context processors."""

from __future__ import annotations

from typing import Any

from django.conf import settings


def settings_globals(request: Any) -> dict[str, Any]:
    """Expose selected settings to templates."""

    return {
        "DEBUG": settings.DEBUG,
        "SWIFT_TELEMETRY": settings.SWIFT_TELEMETRY_SETTINGS(),
    }

