from django.db import IntegrityError

from .models import Libro, Reserva, Socio


def registrar_libro(isbn, titulo, autor, anio_publicacion, cantidad):
    libro = Libro(
        isbn=isbn,
        titulo=titulo,
        autor=autor,
        anio_publicacion=anio_publicacion,
        cantidad_total=cantidad,
        cantidad_disponible=cantidad,
    )
    libro.full_clean()
    libro.save()
    return libro


def registrar_socio(numero_socio, nombre, apellido, dni, email):
    socio = Socio(
        numero_socio=numero_socio,
        nombre=nombre,
        apellido=apellido,
        dni=dni,
        email=email,
    )
    socio.full_clean()
    socio.save()
    return socio


def buscar_libros(texto):
    por_isbn = Libro.objects.filter(isbn__iexact=texto)
    if por_isbn.exists():
        return por_isbn
    return Libro.objects.filter(titulo__icontains=texto) | Libro.objects.filter(
        autor__icontains=texto
    )


def libros_disponibles():
    return Libro.objects.filter(cantidad_disponible__gt=0)


def libros_sin_disponibilidad():
    return Libro.objects.filter(cantidad_disponible=0)


def reservas_pendientes():
    return Reserva.objects.filter(estado=Reserva.Estado.PENDIENTE)


def reservas_de_socio(numero_socio):
    return Reserva.objects.filter(socio__numero_socio=numero_socio)


def reservas_de_libro(isbn):
    return Reserva.objects.filter(libro__isbn=isbn)


def socios_activos():
    return Socio.objects.filter(activo=True)


def historial_reservas_socio(numero_socio):
    return reservas_de_socio(numero_socio).order_by("fecha_reserva")


def realizar_reserva(numero_socio, isbn):
    socio = Socio.objects.get(numero_socio=numero_socio)
    libro = Libro.objects.get(isbn=isbn)
    try:
        return Reserva.crear(socio, libro)
    except IntegrityError as error:
        raise ValueError("El socio ya tiene una reserva activa de este libro.") from error


def cancelar_reserva(numero_reserva):
    reserva = Reserva.objects.get(pk=numero_reserva)
    reserva.cancelar()
    return reserva


def retirar_reserva(numero_reserva):
    reserva = Reserva.objects.get(pk=numero_reserva)
    reserva.retirar()
    return reserva


def devolver_reserva(numero_reserva):
    reserva = Reserva.objects.get(pk=numero_reserva)
    reserva.finalizar()
    return reserva
