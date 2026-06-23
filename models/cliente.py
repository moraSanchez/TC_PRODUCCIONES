from config.database import DatabaseConnection
from models.usuario import Usuario

class Cliente(Usuario):
    def __init__(self, id_usuario=None, nombre=None, apellido=None, email=None, contrasenia=None):
        super().__init__(id_usuario, nombre, apellido, email, contrasenia, tipo='Cliente')

    # ─────────────────────────────────────────────
    # RFMC1 / RFMC2: guardar (registro) — heredado de Usuario vía auth_controller
    # ─────────────────────────────────────────────
    def guardar(self):
        """Persiste un nuevo cliente en la BD."""
        db = DatabaseConnection()
        cursor = db.get_cursor()
        if cursor:
            try:
                cursor.execute(
                    "INSERT INTO Usuario (nombre, apellido, email, contrasenia, tipo) VALUES (%s, %s, %s, %s, 'Cliente')",
                    (self.nombre, self.apellido, self.email, self.contrasenia)
                )
                db.commit()
                self.id_usuario = cursor.lastrowid
                cursor.close()
                return True
            except Exception as e:
                print(f"Error al guardar Cliente: {e}")
                cursor.close()
        return False

    # ─────────────────────────────────────────────
    # RFMC4 (perfil): obtener datos del usuario autenticado
    # ─────────────────────────────────────────────
    @classmethod
    def obtener_perfil(cls, id_usuario):
        """
        Devuelve un dict con los datos del usuario (sin contraseña).
        Usado por el panel de perfil en el navbar.
        """
        db = DatabaseConnection()
        cursor = db.get_cursor()
        if cursor:
            try:
                cursor.execute(
                    "SELECT idUsuario, nombre, apellido, email, tipo FROM Usuario WHERE idUsuario = %s",
                    (id_usuario,)
                )
                resultado = cursor.fetchone()
                cursor.close()
                return resultado  # dict gracias al cursor(dictionary=True)
            except Exception as e:
                print(f"Error al obtener perfil: {e}")
                cursor.close()
        return None

    # ─────────────────────────────────────────────
    # RFMC4 (edición): actualizar nombre y apellido
    # ─────────────────────────────────────────────
    @classmethod
    def actualizar_nombre(cls, id_usuario, nombre, apellido):
        """
        Actualiza nombre y apellido del cliente.
        Retorna True si tuvo éxito, False si falló.
        """
        if not nombre or not nombre.strip():
            return False, "El nombre no puede estar vacío."

        db = DatabaseConnection()
        cursor = db.get_cursor()
        if cursor:
            try:
                cursor.execute(
                    "UPDATE Usuario SET nombre = %s, apellido = %s WHERE idUsuario = %s AND tipo = 'Cliente'",
                    (nombre.strip(), apellido.strip() if apellido else '', id_usuario)
                )
                db.commit()
                cursor.close()
                return True, "Datos actualizados correctamente."
            except Exception as e:
                print(f"Error al actualizar nombre: {e}")
                cursor.close()
        return False, "Error interno al actualizar."

    # ─────────────────────────────────────────────
    # RFMC11: historial de reservas del usuario
    # ─────────────────────────────────────────────
    @classmethod
    def obtener_historial_reservas(cls, id_usuario):
        """
        Devuelve todas las reservas del cliente con detalle completo:
        película, función, sala, asientos, total y estado de pago.
        """
        db = DatabaseConnection()
        cursor = db.get_cursor()
        if cursor:
            try:
                cursor.execute("""
                    SELECT
                        r.idReserva,
                        r.fecha_reserva,
                        r.total,
                        r.estado_pago,
                        p.titulo          AS pelicula_titulo,
                        p.imagen_url      AS pelicula_imagen,
                        p.genero          AS pelicula_genero,
                        f.fecha           AS funcion_fecha,
                        f.hora            AS funcion_hora,
                        f.formato         AS funcion_formato,
                        COALESCE(f.idioma, 'Doblada') AS funcion_idioma,
                        f.Sala_idSala     AS num_sala,
                        GROUP_CONCAT(
                            CONCAT(a.fila, a.numero)
                            ORDER BY a.fila, a.numero
                            SEPARATOR ', '
                        ) AS asientos
                    FROM Reserva r
                    JOIN Funcion  f  ON r.Funcion_idFuncion  = f.idFuncion
                    JOIN Pelicula p  ON f.Pelicula_idPelicula = p.idPelicula
                    LEFT JOIN ReservaAsiento ra ON ra.Reserva_idReserva = r.idReserva
                    LEFT JOIN Asiento a         ON a.idAsiento = ra.Asiento_idAsiento
                    WHERE r.Usuario_idUsuario = %s
                    GROUP BY r.idReserva
                    ORDER BY r.fecha_reserva DESC
                """, (id_usuario,))

                reservas = cursor.fetchall()
                cursor.close()

                # Normalizar tipos no serializables para JSON
                resultado = []
                for res in reservas:
                    item = dict(res)
                    # timedelta → string legible
                    if hasattr(item.get('funcion_hora'), 'total_seconds'):
                        seg = item['funcion_hora'].seconds
                        item['funcion_hora'] = f"{seg // 3600:02d}:{(seg % 3600) // 60:02d}"
                    else:
                        item['funcion_hora'] = str(item.get('funcion_hora', ''))[:5]
                    # date → string
                    if item.get('funcion_fecha'):
                        item['funcion_fecha'] = str(item['funcion_fecha'])
                    if item.get('fecha_reserva'):
                        item['fecha_reserva'] = str(item['fecha_reserva'])
                    # Decimal → float
                    if item.get('total') is not None:
                        item['total'] = float(item['total'])
                    resultado.append(item)

                return resultado
            except Exception as e:
                print(f"Error al obtener historial: {e}")
                cursor.close()
        return []

    # ─────────────────────────────────────────────
    # RFMC9 / RFMC10: cancelar una reserva propia
    # ─────────────────────────────────────────────
    @classmethod
    def cancelar_reserva(cls, id_reserva, id_usuario):
        """
        Cancela una reserva verificando que pertenezca al usuario.
        Solo se puede cancelar si el estado_pago NO es 'cancelado'.
        Retorna (True, mensaje) o (False, mensaje).
        """
        db = DatabaseConnection()
        cursor = db.get_cursor()
        if cursor:
            try:
                # Verificar que la reserva pertenece al usuario
                cursor.execute(
                    "SELECT idReserva, estado_pago FROM Reserva WHERE idReserva = %s AND Usuario_idUsuario = %s",
                    (id_reserva, id_usuario)
                )
                reserva = cursor.fetchone()

                if not reserva:
                    cursor.close()
                    return False, "Reserva no encontrada o no pertenece a este usuario."

                if reserva['estado_pago'] == 'cancelado':
                    cursor.close()
                    return False, "Esta reserva ya fue cancelada anteriormente."

                # Marcar como cancelado
                cursor.execute(
                    "UPDATE Reserva SET estado_pago = 'cancelado' WHERE idReserva = %s",
                    (id_reserva,)
                )
                db.commit()
                cursor.close()
                return True, "Reserva cancelada correctamente."

            except Exception as e:
                print(f"Error al cancelar reserva: {e}")
                cursor.close()
        return False, "Error interno al cancelar la reserva."