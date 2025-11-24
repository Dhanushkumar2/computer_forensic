from django.apps import AppConfig


class ForensicApiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'forensic_api'
    verbose_name = 'Forensic Investigation API'
    
    def ready(self):
        """Initialize the app when Django starts"""
        import forensic_api.signals