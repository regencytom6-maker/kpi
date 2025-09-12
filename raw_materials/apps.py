from django.apps import AppConfig


class RawMaterialsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'raw_materials'
    verbose_name = 'Raw Materials Inventory'

    def ready(self):
        import raw_materials.signals
