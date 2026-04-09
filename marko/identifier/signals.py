from django.db.models.signals import pre_delete
from django.dispatch import receiver
from django.core.exceptions import ValidationError
from .models import TypeId


@receiver(pre_delete, sender=TypeId)
def prevent_deleting_protected_typeid(sender, instance, **kwargs):
    if instance.name.lower() in ['qrcode', 'barcode']:
        raise ValidationError(f"Impossible de supprimer le TypeId protégé : {instance.name}")
