from django.apps import AppConfig


class NotificationsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "notifications"

    def ready(self) -> None:  # pragma: no cover - import side effects
        from . import signals  # noqa: F401

        return super().ready()
