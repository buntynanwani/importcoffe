from django.apps import AppConfig
import os.path

class BackendConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'Backend'

    def ready(self):
        print("Setup already completed. Skipping setup.")   
