from django.apps import AppConfig


class BackendConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'Backend'

    def ready(self):
        print("Django custom start!")
        return super().ready()