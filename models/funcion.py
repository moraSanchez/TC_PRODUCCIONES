from config.database import DatabaseConnection

class Funcion:
    def __init__(self, id_funcion=None, fecha=None, hora=None,
                 estado='activa', id_pelicula=None, id_sala=None):
        self.id_funcion  = id_funcion
        self.fecha       = fecha
        self.hora        = hora
        self.estado      = estado
        self.id_pelicula = id_pelicula
        self.id_sala     = id_sala

    def obtener_asientos_disponibles(self):
        """Devuelve los asientos no reservados para esta función."""
        db = DatabaseConnection()
        cursor = db.get_cursor()
        if cursor:
            cursor.execute("""
                SELECT a.* FROM Asiento a
                WHERE a.Sala_idSala = %s
                AND a.idAsiento NOT IN (
                    SELECT ra.Asiento_idAsiento
                    FROM ReservaAsiento ra
                    JOIN Reserva r ON ra.Reserva_idReserva = r.idReserva
                    WHERE r.Funcion_idFuncion = %s
                    AND ra.estado = 'reservado'
                )
            """, (self.id_sala, self.id_funcion))
            return cursor.fetchall()
        return []

    def guardar(self):
        db = DatabaseConnection()
        cursor = db.get_cursor()
        if cursor:
            try:
                cursor.execute("""
                    INSERT INTO Funcion (fecha, hora, estado, Pelicula_idPelicula, Sala_idSala)
                    VALUES (%s, %s, %s, %s, %s)
                """, (self.fecha, self.hora, self.estado, self.id_pelicula, self.id_sala))
                db.commit()
                self.id_funcion = cursor.lastrowid
                return True
            except Exception as e:
                print(f"Error al guardar función: {e}")
                return False

    @classmethod
    def buscar_todas(cls):
        db = DatabaseConnection()
        cursor = db.get_cursor()
        if cursor:
            cursor.execute("""
                SELECT f.*, p.titulo, p.genero, s.numero as num_sala
                FROM Funcion f
                JOIN Pelicula p ON f.Pelicula_idPelicula = p.idPelicula
                JOIN Sala s     ON f.Sala_idSala = s.idSala
                WHERE f.estado = 'activa'
            """)
            return cursor.fetchall()
        return []

    def to_dict(self):
        return {
            "idFuncion":  self.id_funcion,
            "fecha":      str(self.fecha),
            "hora":       str(self.hora),
            "estado":     self.estado,
            "idPelicula": self.id_pelicula,
            "idSala":     self.id_sala
        }