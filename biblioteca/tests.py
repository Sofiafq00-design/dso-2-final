from django.core.exceptions import ValidationError
from django.test import TestCase

from .models import Libro, Reserva, Socio
from .services import (
    buscar_libros,
    libros_disponibles,
    libros_sin_disponibilidad,
    realizar_reserva,
    registrar_libro,
)


class ReservaTests(TestCase):
    def setUp(self):
        self.socio = Socio.objects.create(
            numero_socio=1,
            nombre="Ana",
            apellido="Pérez",
            dni="12345678",
            email="ana@example.com",
        )
        self.libro = Libro.objects.create(
            isbn="9780000000001",
            titulo="El nombre de la rosa",
            autor="Umberto Eco",
            anio_publicacion=1980,
            cantidad_total=2,
            cantidad_disponible=2,
        )

    def test_reservar_disminuye_disponibilidad_y_devolver_la_restaura(self):
        reserva = realizar_reserva(self.socio.numero_socio, self.libro.isbn)
        self.libro.refresh_from_db()
        self.assertEqual(self.libro.cantidad_disponible, 1)

        reserva.retirar()
        reserva.finalizar()
        self.libro.refresh_from_db()
        self.assertEqual(reserva.estado, Reserva.Estado.FINALIZADA)
        self.assertEqual(self.libro.cantidad_disponible, 2)

    def test_cancelar_reserva_pendiente_devuelve_ejemplar(self):
        reserva = realizar_reserva(self.socio.numero_socio, self.libro.isbn)
        reserva.cancelar()
        self.libro.refresh_from_db()
        self.assertEqual(reserva.estado, Reserva.Estado.CANCELADA)
        self.assertEqual(self.libro.cantidad_disponible, 2)

    def test_socio_inactivo_no_puede_reservar(self):
        self.socio.activo = False
        self.socio.save()

        with self.assertRaisesMessage(ValueError, "El socio está inactivo"):
            realizar_reserva(self.socio.numero_socio, self.libro.isbn)

    def test_no_se_puede_cancelar_una_reserva_retirada(self):
        reserva = realizar_reserva(self.socio.numero_socio, self.libro.isbn)
        reserva.retirar()

        with self.assertRaisesMessage(ValueError, "Solo se pueden cancelar"):
            reserva.cancelar()

    def test_busqueda_parcial_por_titulo_y_consultas_de_disponibilidad(self):
        self.assertIn(self.libro, buscar_libros("rosa"))
        self.assertIn(self.libro, libros_disponibles())

        self.libro.cantidad_disponible = 0
        self.libro.save()
        self.assertIn(self.libro, libros_sin_disponibilidad())
        self.assertNotIn(self.libro, libros_disponibles())

    def test_registro_rechaza_cantidad_invalida(self):
        with self.assertRaises(ValidationError):
            registrar_libro("9780000000002", "Libro", "Autor", 2020, 0)

    def test_no_se_puede_reservar_sin_stock(self):
        self.libro.cantidad_total = 1
        self.libro.cantidad_disponible = 1
        self.libro.save()
        realizar_reserva(self.socio.numero_socio, self.libro.isbn)
        otro_socio = Socio.objects.create(
            numero_socio=2,
            nombre="Juan",
            apellido="Gómez",
            dni="87654321",
            email="juan@example.com",
        )

        with self.assertRaisesMessage(ValueError, "No hay ejemplares disponibles"):
            realizar_reserva(otro_socio.numero_socio, self.libro.isbn)

    def test_no_se_puede_repetir_reserva_activa(self):
        realizar_reserva(self.socio.numero_socio, self.libro.isbn)

        with self.assertRaisesMessage(ValueError, "ya tiene una reserva activa"):
            realizar_reserva(self.socio.numero_socio, self.libro.isbn)
