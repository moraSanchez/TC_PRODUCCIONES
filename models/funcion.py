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

    def actualizar(self):
        db = DatabaseConnection()
        cursor = db.get_cursor()
        if cursor:
            try:
                cursor.execute("""
                    UPDATE Funcion 
                    SET fecha = %s, hora = %s, Pelicula_idPelicula = %s, Sala_idSala = %s
                    WHERE idFuncion = %s
                """, (self.fecha, self.hora, self.id_pelicula, self.id_sala, self.id_funcion))
                db.commit()
                return True
            except Exception as e:
                print(f"Error al actualizar función: {e}")
                return False

    def eliminar(self):
        db = DatabaseConnection()
        cursor = db.get_cursor()
        if cursor:
            try:
                cursor.execute("DELETE FROM Funcion WHERE idFuncion = %s", (self.id_funcion,))
                db.commit()
                return True
            except Exception as e:
                print(f"Error al eliminar función: {e}")
                return False

    @classmethod
    def buscar_todas(cls):
        db = DatabaseConnection()
        cursor = db.get_cursor()
        if cursor:
            cursor.execute("""
                SELECT f.idFuncion, f.fecha, f.hora, f.estado, 
                       p.titulo, p.genero, s.numero as num_sala
                FROM Funcion f
                JOIN Pelicula p ON f.Pelicula_idPelicula = p.idPelicula
                JOIN Sala s     ON f.Sala_idSala = s.idSala
                ORDER BY f.fecha ASC, f.hora ASC
            """)
            return cursor.fetchall()
        return []