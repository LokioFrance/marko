from django.db import models
from django.core.exceptions import ValidationError
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings

import qrcode
import barcode
from barcode.writer import ImageWriter
from io import BytesIO
from django.core.files.base import ContentFile


class TypeId(models.Model):
    name = models.CharField(max_length=50, unique=True)

    PROTECTED_NAMES = ['qrcode', 'barcode']

    def delete(self, *args, **kwargs):
        if self.name in self.PROTECTED_NAMES:
            raise ValidationError(f"{self.name} ne peut pas être supprimé.")
        super().delete(*args, **kwargs)

    def __str__(self):
        return self.name


class Identifier(models.Model):
    id_type = models.ForeignKey(
        TypeId,
        on_delete=models.PROTECT,
        related_name='identifiers'
    )

    id_item = models.PositiveIntegerField()

    img = models.ImageField(
        upload_to='identifiers/',
        null=True,
        blank=True,
        unique=True
    )

    value = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        unique=True
    )

    def __str__(self):
        return f"{self.id_type.name} - {self.id_item}"


def generate_qrcode(identifier):
    base_url = "https://example.com"  # à adapter plus tard
    data = f"{base_url}/{identifier.id_item}"

    qr = qrcode.make(data)
    buffer = BytesIO()
    qr.save(buffer, format='PNG')

    filename = f"qrcode_{identifier.id_item}.png"
    identifier.img.save(filename, ContentFile(buffer.getvalue()), save=False)


def generate_barcode(identifier):
    CODE128 = barcode.get_barcode_class('code128')
    code = CODE128(str(identifier.id_item), writer=ImageWriter())

    buffer = BytesIO()
    code.write(buffer)

    filename = f"barcode_{identifier.id_item}.png"
    identifier.img.save(filename, ContentFile(buffer.getvalue()), save=False)


@receiver(post_save, sender=Identifier)
def create_identifier_image(sender, instance, created, **kwargs):
    if not created or instance.img:
        return

    type_name = instance.id_type.name.lower()

    if type_name == 'qrcode':
        generate_qrcode(instance)

    elif type_name == 'barcode':
        generate_barcode(instance)

    instance.save()
