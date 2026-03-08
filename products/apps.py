from django.apps import AppConfig


class ProductsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'products'
    
    def ready(self):
        import products.signals
        
        from django.contrib.auth.models import Permission
        from django.contrib.contenttypes.models import ContentType
        
        try:
            from .models import Produs
            content_type = ContentType.objects.get_for_model(Produs)
            Permission.objects.get_or_create(
                codename='vizualizeaza_oferta',
                name='Poate vizualiza oferta speciala',
                content_type=content_type
            )
        except:
            pass
