from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from identifier.models import Identifier, TypeId


class TypeIdTests(APITestCase):
    def setUp(self):
        self.qrcode = TypeId.objects.get_or_create(name="qrcode")[0]
        self.barcode = TypeId.objects.get_or_create(name="barcode")[0]

    # ── LIST ──────────────────────────────────────────────────────────────────

    def test_list_typeids(self):
        response = self.client.get(reverse("typeid-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 2)

    # ── CREATE ────────────────────────────────────────────────────────────────

    def test_create_typeid(self):
        response = self.client.post(reverse("typeid-list"), {"name": "rfid"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(TypeId.objects.filter(name="rfid").exists())

    def test_create_typeid_duplicate(self):
        response = self.client.post(reverse("typeid-list"), {"name": "qrcode"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # ── RETRIEVE ──────────────────────────────────────────────────────────────

    def test_retrieve_typeid(self):
        response = self.client.get(reverse("typeid-detail", args=[self.qrcode.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], "qrcode")

    def test_retrieve_typeid_not_found(self):
        response = self.client.get(reverse("typeid-detail", args=[9999]))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    # ── UPDATE ────────────────────────────────────────────────────────────────

    def test_update_typeid(self):
        rfid = TypeId.objects.create(name="rfid")
        response = self.client.put(
            reverse("typeid-detail", args=[rfid.id]), {"name": "rfid-v2"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_partial_update_typeid(self):
        rfid = TypeId.objects.create(name="nfc")
        response = self.client.patch(
            reverse("typeid-detail", args=[rfid.id]), {"name": "nfc-v2"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    # ── DELETE ────────────────────────────────────────────────────────────────

    def test_delete_typeid(self):
        rfid = TypeId.objects.create(name="delete-me")
        response = self.client.delete(reverse("typeid-detail", args=[rfid.id]))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_delete_protected_typeid_qrcode(self):
        """qrcode et barcode ne peuvent pas être supprimés."""
        response = self.client.delete(reverse("typeid-detail", args=[self.qrcode.id]))
        self.assertNotEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertTrue(TypeId.objects.filter(name="qrcode").exists())


class IdentifierTests(APITestCase):
    def setUp(self):
        self.typeid = TypeId.objects.get_or_create(name="custom")[0]
        self.identifier = Identifier.objects.create(
            id_type=self.typeid,
            id_item=42,
            value="test-value-42",
        )

    # ── LIST ──────────────────────────────────────────────────────────────────

    def test_list_identifiers(self):
        response = self.client.get(reverse("identifier-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 1)

    def test_filter_by_id_item(self):
        Identifier.objects.create(id_type=self.typeid, id_item=99, value="other-99")
        response = self.client.get(reverse("identifier-list"), {"id_item": 42})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    # ── CREATE ────────────────────────────────────────────────────────────────

    def test_create_identifier(self):
        payload = {"id_type": "custom", "id_item": 7, "value": "unique-7"}
        response = self.client.post(reverse("identifier-list"), payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_identifier_invalid_type(self):
        payload = {"id_type": "inexistant", "id_item": 1}
        response = self.client.post(reverse("identifier-list"), payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_identifier_duplicate_value(self):
        payload = {"id_type": "custom", "id_item": 43, "value": "test-value-42"}
        response = self.client.post(reverse("identifier-list"), payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # ── RETRIEVE ──────────────────────────────────────────────────────────────

    def test_retrieve_identifier(self):
        response = self.client.get(reverse("identifier-detail", args=[self.identifier.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id_item"], 42)

    def test_retrieve_identifier_not_found(self):
        response = self.client.get(reverse("identifier-detail", args=[9999]))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    # ── UPDATE ────────────────────────────────────────────────────────────────

    def test_partial_update_identifier(self):
        response = self.client.patch(
            reverse("identifier-detail", args=[self.identifier.id]),
            {"value": "updated-value"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    # ── DELETE ────────────────────────────────────────────────────────────────

    def test_delete_identifier(self):
        response = self.client.delete(
            reverse("identifier-detail", args=[self.identifier.id])
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(
            Identifier.objects.filter(id=self.identifier.id).count(), 0
        )
