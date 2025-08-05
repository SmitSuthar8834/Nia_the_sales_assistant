from django.apps import AppConfig


class AdminConfigConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'admin_config'
    verbose_name = 'Admin Configuration'
    
    def ready(self):
        # Import signal handlers
        try:
            import admin_config.signals
        except ImportError:
            pass