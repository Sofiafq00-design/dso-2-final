from django.core.management.base import BaseCommand
from django.db import IntegrityError
from django.core.exceptions import ValidationError

from biblioteca.models import Libro, Reserva, Socio
from biblioteca.services import (
    buscar_libros,
    cancelar_reserva,
    devolver_reserva,
    registrar_libro,
    registrar_socio,
    realizar_reserva,
    retirar_reserva,
)


class Command(BaseCommand):
    help = "Abre el menú de gestión de la biblioteca en la consola."

    def handle(self, *args, **options):
        while True:
            self.mostrar_menu()
            opcion = input("Elegí una opción: ").strip()
            acciones = {
                "1": self.registrar_libro,
                "2": self.registrar_socio,
                "3": self.listar_libros,
                "4": self.buscar_libro,
                "5": self.listar_socios,
                "6": self.realizar_reserva,
                "7": self.cancelar_reserva,
                "8": self.retirar_libro,
                "9": self.devolver_libro,
                "10": self.listar_reservas_socio,
                "11": self.listar_reservas,
            }
            if opcion == "0":
                self.stdout.write("Hasta luego.")
                break

            accion = acciones.get(opcion)
            if accion is None:
                self.stdout.write(self.style.ERROR("Opción incorrecta."))
                continue
            try:
                accion()
            except (ValueError, IntegrityError, ValidationError) as error:
                self.stdout.write(self.style.ERROR(f"Error: {error}"))
            except (Libro.DoesNotExist, Socio.DoesNotExist, Reserva.DoesNotExist):
                self.stdout.write(self.style.ERROR("No se encontró el dato solicitado."))
            input("\nPresioná Enter para continuar...")

    def mostrar_menu(self):
        self.stdout.write(
            "\n=============================\n"
            "BIBLIOTECA\n"
            "=============================\n"
            "1. Registrar libro\n"
            "2. Registrar socio\n"
            "3. Listar libros\n"
            "4. Buscar libro\n"
            "5. Listar socios\n"
            "6. Realizar reserva\n"
            "7. Cancelar reserva\n"
            "8. Retirar libro reservado\n"
            "9. Devolver libro\n"
            "10. Listar reservas de un socio\n"
            "11. Listar todas las reservas\n"
            "0. Salir"
        )

    def registrar_libro(self):
        isbn = input("ISBN: ").strip()
        titulo = input("Título: ").strip()
        autor = input("Autor: ").strip()
        anio = int(input("Año de publicación: "))
        cantidad = int(input("Cantidad de ejemplares: "))
        libro = registrar_libro(isbn, titulo, autor, anio, cantidad)
        self.stdout.write(self.style.SUCCESS(f"Libro registrado: {libro}"))

    def registrar_socio(self):
        numero = int(input("Número de socio: "))
        nombre = input("Nombre: ").strip()
        apellido = input("Apellido: ").strip()
        dni = input("DNI: ").strip()
        email = input("Email: ").strip()
        socio = registrar_socio(numero, nombre, apellido, dni, email)
        self.stdout.write(self.style.SUCCESS(f"Socio registrado: {socio}"))

    def listar_libros(self):
        libros = Libro.objects.all()
        if not libros.exists():
            self.stdout.write("No hay libros registrados.")
        for libro in libros:
            self.stdout.write(
                f"{libro.isbn} | {libro.titulo} | {libro.autor} | "
                f"{libro.cantidad_disponible}/{libro.cantidad_total} disponibles"
            )

    def buscar_libro(self):
        texto = input("ISBN, título o autor: ").strip()
        libros = buscar_libros(texto)
        for libro in libros.distinct():
            self.stdout.write(
                f"{libro.isbn} | {libro.titulo} | {libro.autor} | "
                f"{libro.cantidad_disponible}/{libro.cantidad_total} disponibles"
            )
        if not libros.exists():
            self.stdout.write("No se encontraron libros.")

    def listar_socios(self):
        socios = Socio.objects.all()
        if not socios.exists():
            self.stdout.write("No hay socios registrados.")
        for socio in socios:
            estado = "Activo" if socio.activo else "Inactivo"
            self.stdout.write(f"{socio} | DNI: {socio.dni} | {estado}")

    def realizar_reserva(self):
        numero = int(input("Número de socio: "))
        isbn = input("ISBN del libro: ").strip()
        reserva = realizar_reserva(numero, isbn)
        self.stdout.write(self.style.SUCCESS(f"Reserva realizada. Número: {reserva.pk}"))

    def cancelar_reserva(self):
        reserva = cancelar_reserva(int(input("Número de reserva: ")))
        self.stdout.write(self.style.SUCCESS(f"Reserva {reserva.pk} cancelada."))

    def retirar_libro(self):
        reserva = retirar_reserva(int(input("Número de reserva: ")))
        self.stdout.write(self.style.SUCCESS(f"Reserva {reserva.pk} marcada como retirada."))

    def devolver_libro(self):
        reserva = devolver_reserva(int(input("Número de reserva: ")))
        self.stdout.write(self.style.SUCCESS(f"Reserva {reserva.pk} finalizada."))

    def listar_reservas_socio(self):
        numero = int(input("Número de socio: "))
        socio = Socio.objects.get(numero_socio=numero)
        reservas = Reserva.objects.filter(socio=socio)
        self.imprimir_reservas(reservas)

    def listar_reservas(self):
        self.imprimir_reservas(Reserva.objects.select_related("socio", "libro"))

    def imprimir_reservas(self, reservas):
        if not reservas.exists():
            self.stdout.write("No hay reservas para mostrar.")
        for reserva in reservas:
            self.stdout.write(
                f"N.º {reserva.pk} | {reserva.socio} | {reserva.libro.titulo} | "
                f"{reserva.get_estado_display()} | "
                f"{reserva.fecha_reserva.strftime('%d/%m/%Y %H:%M')}"
            )
