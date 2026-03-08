from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings
from .models import Comanda, ProdusComanda, Nota


@receiver(post_save, sender=Comanda)
def trimite_email_rating(sender, instance, created, **kwargs):
    if created:
        pass
