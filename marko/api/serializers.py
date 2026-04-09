from rest_framework import serializers

from api.models import HoneypotAttempt
from identifier.models import Identifier, TypeId


class TypeIdSerializer(serializers.ModelSerializer):
    class Meta:
        model = TypeId
        fields = ['id', 'name']


class IdentifierSerializer(serializers.ModelSerializer):
    id_type = serializers.SlugRelatedField(
        slug_field='name', queryset=TypeId.objects.all()
    )

    class Meta:
        model = Identifier
        fields = ['id', 'id_type', 'id_item', 'img', 'value']
        read_only_fields = ['img']


class HoneypotAttemptSerializer(serializers.ModelSerializer):
    class Meta:
        model = HoneypotAttempt
        fields = ["id", "ip", "user_agent", "path", "method", "username", "timestamp"]
