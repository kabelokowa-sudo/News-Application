from django.apps import AppConfig


class NewsConfig(AppConfig):
    """Django app configuration for the news app.

    Registers the ``news.signals`` module on app startup so the
    ``sync_user_role`` signal receiver is connected.
    """

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'news'

    def ready(self):
        import news.signals  # noqa: F401  (import registers the receiver)
