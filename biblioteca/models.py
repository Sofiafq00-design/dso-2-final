from django.core.validators import MinValueValidator
from django.db import models, transaction
from django.db.models import Q


class Libro(models.Model):
    isbn = models.CharField(max_length=20, unique=True)
    titulo = models.CharField(max_length=200)
    autor = models.CharField(max_length=150)
    anio_publicacion = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1)]
    )
    cantidad_total = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    cantidad_disponible = models.PositiveIntegerField()

    class Meta:
        ordering = ["titulo"]
        constraints = [
            models.CheckConstraint(
                condition=Q(
                    cantidad_total__gte=1,
                    cantidad_disponible__lte=models.F("cantidad_total"),
                ),
                name="disponibles_no_superan_total",
            ),
        ]

    def __str__(self):
        return f"{self.titulo} - {self.autor}"

    def quitar_ejemplar(self):
        if self.cantidad_disponible <= 0:
            raise ValueError("No hay ejemplares disponibles.")
        self.cantidad_disponible -= 1
        self.save(update_fields=["cantidad_disponible"])

    def agregar_ejemplar(self):
        if self.cantidad_disponible >= self.cantidad_total:
            raise ValueError("La cantidad disponible ya llegó al total.")
        self.cantidad_disponible += 1
        self.save(update_fields=["cantidad_disponible"])


class Socio(models.Model):
    numero_socio = models.PositiveIntegerField(unique=True)
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    dni = models.CharField(max_length=20, unique=True)
    email = models.EmailField()
    activo = models.BooleanField(default=True)

    class Meta:
        ordering = ["apellido", "nombre"]

    def __str__(self):
        return f"{self.numero_socio} - {self.apellido}, {self.nombre}"


class Reserva(models.Model):
    class Estado(models.TextChoices):
        PENDIENTE = "PENDIENTE", "Pendiente"
        RETIRADA = "RETIRADA", "Retirada"
        CANCELADA = "CANCELADA", "Cancelada"
        FINALIZADA = "FINALIZADA", "Finalizada"

    socio = models.ForeignKey(Socio, on_delete=models.PROTECT, related_name="reservas")
    libro = models.ForeignKey(Libro, on_delete=models.PROTECT, related_name="reservas")
    fecha_reserva = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(
        max_length=10,
        choices=Estado.choices,
        default=Estado.PENDIENTE,
    )

    class Meta:
        ordering = ["-fecha_reserva"]
        constraints = [
            models.UniqueConstraint(
                fields=["socio", "libro"],
                condition=Q(estado__in=["PENDIENTE", "RETIRADA"]),
                name="una_reserva_activa_por_libro",
            ),
        ]

    def __str__(self):
        return f"Reserva {self.id}: {self.libro} ({self.get_estado_display()})"

    @classmethod
    def crear(cls, socio, libro):
        with transaction.atomic():
            socio = Socio.objects.get(pk=socio.pk)
            libro = Libro.objects.select_for_update().get(pk=libro.pk)

            if not socio.activo:
                raise ValueError("El socio está inactivo y no puede reservar.")
            if cls.objects.filter(
                socio=socio,
                libro=libro,
                estado__in=[cls.Estado.PENDIENTE, cls.Estado.RETIRADA],
            ).exists():
                raise ValueError("El socio ya tiene una reserva activa de este libro.")

            libro.quitar_ejemplar()
            return cls.objects.create(socio=socio, libro=libro)

    def cancelar(self):
        with transaction.atomic():
            reserva = Reserva.objects.select_for_update().get(pk=self.pk)
            if reserva.estado != self.Estado.PENDIENTE:
                raise ValueError("Solo se pueden cancelar reservas pendientes.")

            libro = Libro.objects.select_for_update().get(pk=reserva.libro_id)
            libro.agregar_ejemplar()
            reserva.estado = self.Estado.CANCELADA
            reserva.save(update_fields=["estado"])
            self.estado = reserva.estado

    def retirar(self):
        with transaction.atomic():
            reserva = Reserva.objects.select_for_update().get(pk=self.pk)
            if reserva.estado != self.Estado.PENDIENTE:
                raise ValueError("Solo se pueden retirar reservas pendientes.")
            reserva.estado = self.Estado.RETIRADA
            reserva.save(update_fields=["estado"])
            self.estado = reserva.estado

    def finalizar(self):
        with transaction.atomic():
            reserva = Reserva.objects.select_for_update().get(pk=self.pk)
            if reserva.estado != self.Estado.RETIRADA:
                raise ValueError("Solo se pueden devolver libros que fueron retirados.")

            libro = Libro.objects.select_for_update().get(pk=reserva.libro_id)
            libro.agregar_ejemplar()
            reserva.estado = self.Estado.FINALIZADA
            reserva.save(update_fields=["estado"])
            self.estado = reserva.estado
