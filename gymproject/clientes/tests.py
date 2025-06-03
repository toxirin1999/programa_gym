from django.test import TestCase

from .models import Cliente, RevisionProgreso


class RevisionProgresoTests(TestCase):
    def setUp(self):
        self.cliente = Cliente.objects.create(
            nombre="Test Cliente",
            email="test@example.com",
            telefono="123456789",
        )

    def test_check_alerts_no_alerts(self):
        revision = RevisionProgreso(
            cliente=self.cliente,
            grasa_corporal=25,
            peso_corporal=70,
        )
        self.assertIsNone(revision.check_alerts())

    def test_check_alerts_with_alerts(self):
        revision = RevisionProgreso(
            cliente=self.cliente,
            grasa_corporal=35,
            peso_corporal=45,
        )
        self.assertEqual(
            revision.check_alerts(),
            ["Grasa corporal alta", "Peso corporal muy bajo"],
        )

