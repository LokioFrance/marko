from django.apps import AppConfig


class IdentifierConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'identifier'

    def ready(self):
        # Importer les signals pour qu'ils soient enregistrés
        import identifier.signals
