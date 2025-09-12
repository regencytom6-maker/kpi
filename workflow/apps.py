from django.apps import AppConfig


class WorkflowConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'workflow'

    def ready(self):
        # Import signals to register signal handlers
        from . import signals
