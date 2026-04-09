import os

from rest_framework import status, viewsets
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from api.models import HoneypotAttempt
from identifier.models import Identifier, TypeId

from .serializers import (
    HoneypotAttemptSerializer,
    IdentifierSerializer,
    TypeIdSerializer,
)


class TypeIdViewSet(viewsets.ModelViewSet):
    """CRUD pour les types d'identifiants (qrcode, barcode, …)."""

    queryset = TypeId.objects.all()
    serializer_class = TypeIdSerializer
    http_method_names = ['get', 'post', 'put', 'patch', 'delete']


class IdentifierViewSet(viewsets.ModelViewSet):
    """CRUD pour les identifiants générés (QR codes, barcodes)."""

    queryset = Identifier.objects.select_related("id_type").all()
    serializer_class = IdentifierSerializer
    http_method_names = ['get', 'post', 'put', 'patch', 'delete']

    def get_queryset(self):
        qs = super().get_queryset()
        id_item = self.request.query_params.get("id_item")
        if id_item:
            qs = qs.filter(id_item=id_item)
        return qs


class HoneypotView(APIView):
    """
    GET /api/honeypot/

    Retourne toutes les tentatives enregistrées par le honeypot.
    Protégé par l'en-tête X-Honeypot-Key (valeur = HONEYPOT_API_KEY).
    """

    permission_classes = [AllowAny]

    def get(self, request):
        expected_key = os.environ.get("HONEYPOT_API_KEY", "")
        if not expected_key:
            return Response(
                {"detail": "HONEYPOT_API_KEY non configurée sur ce service."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        provided_key = request.headers.get("X-Honeypot-Key", "")
        if provided_key != expected_key:
            return Response(
                {"detail": "Non autorisé."}, status=status.HTTP_403_FORBIDDEN
            )

        attempts = HoneypotAttempt.objects.all()
        serializer = HoneypotAttemptSerializer(attempts, many=True)
        return Response(serializer.data)
