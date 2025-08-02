from django.apps import AppConfig

class KampalaPharmaConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'kampala_pharma'
    
    def ready(self):
        # Import admin configuration when the app is ready
        try:
            from . import admin
        except ImportError:
            pass
