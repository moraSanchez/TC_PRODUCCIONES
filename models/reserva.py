import uuid
from datetime import date
from config.database import DatabaseConnection

class ReservaAsiento:
    """Tabla pivote entre Reserva y Asiento."""
    def __init__(self, id_reserva, id_asiento, precio):
        self.id_reserva = id_reserva
        self.id_asiento = id_asiento
        self.precio     = precio

    def guardar(self):
        db = DatabaseConnection()
        cursor = db.get_cursor()
        if cursor:
            try:
                cursor.execute("""
                    INSERT INTO ReservaAsiento
                    (Reserva_idReserva, Asiento_idAsiento, precio, estado)
                    VALUES (%s, %s, %s, 'reservado')
                """, (self.id_reserva, self.id_asiento, self.precio))
                db.commit()
                return True
            except Exception as e:
                print(f"Error al guardar ReservaAsiento: {e}")
                return False

class Reserva:
    """
    AGREGACIÓN: recibe Cliente y Funcion como objetos externos.
    Ambos existen independientemente de la Reserva.
    """
    def __init__(self, id_reserva=None, cliente=None, funcion=None, estado='pendiente'):
        self.id_reserva   = id_reserva
        self.cliente      = cliente   # Agregación
        self.funcion      = funcion   # Agregación
        self.estado       = estado
        self.reserva_asientos = []    # Composición: ReservaAsiento vive dentro de Reserva

    def agregar_asiento(self, id_asiento, precio):
        ra = ReservaAsiento(self.id_reserva, id_asiento, precio)
        if ra.guardar():
            self.reserva_asientos.append(ra)
            return True
        return False

    def guardar(self):
        db = DatabaseConnection()
        cursor = db.get_cursor()
        if cursor:
            try:
                cursor.execute("""
                    INSERT INTO Reserva (fecha, estado, Usuario_idUsuario, Funcion_idFuncion)
                    VALUES (%s, %s, %s, %s)
                """, (date.today(), self.estado,
                      self.cliente.id_usuario, self.funcion.id_funcion))
                db.commit()
                self.id_reserva = cursor.lastrowid
                return True
            except Exception as e:
                print(f"Error al guardar reserva: {e}")
                return False

    def confirmar(self, metodo_pago='efectivo'):
        """Confirma la reserva, genera Ticket y Pago."""
        db = DatabaseConnection()
        cursor = db.get_cursor()
        if cursor:
            try:
                # Actualizar estado reserva
                cursor.execute(
                    "UPDATE Reserva SET estado='confirmada' WHERE idReserva=%s",
                    (self.id_reserva,)
                )
                # Generar Ticket
                codigo = str(uuid.uuid4()).upper()[:12]
                cursor.execute("""
                    INSERT INTO Ticket (codigo, fecha, Reserva_idReserva)
                    VALUES (%s, %s, %s)
                """, (codigo, date.today(), self.id_reserva))
                # Generar Pago
                cursor.execute("""
                    INSERT INTO Pago (metodo, estado, Reserva_idReserva)
                    VALUES (%s, 'aprobado', %s)
                """, (metodo_pago, self.id_reserva))
                db.commit()
                self.estado = 'confirmada'
                return {"ticket": codigo}
            except Exception as e:
                print(f"Error al confirmar reserva: {e}")
                return None

    @classmethod
    def buscar_por_usuario(cls, id_usuario):
        db = DatabaseConnection()
        cursor = db.get_cursor()
        if cursor:
            cursor.execute("""
                SELECT r.idReserva, r.fecha, r.estado,
                       f.hora, p.titulo,
                       t.codigo as ticket
                FROM Reserva r
                JOIN Funcion f  ON r.Funcion_idFuncion = f.idFuncion
                JOIN Pelicula p ON f.Pelicula_idPelicula = p.idPelicula
                LEFT JOIN Ticket t ON t.Reserva_idReserva = r.idReserva
                WHERE r.Usuario_idUsuario = %s
                ORDER BY r.fecha DESC
            """, (id_usuario,))
            return cursor.fetchall()
        return []