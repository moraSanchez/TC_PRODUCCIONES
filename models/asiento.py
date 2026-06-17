from config.database import DatabaseConnection

class Asiento:
    def __init__(self, id_asiento=None, fila=None, numero=None, id_sala=None):
        self.id_asiento = id_asiento
        self.fila       = fila
        self.numero     = numero
        self.id_sala    = id_sala

    def guardar(self):
        db = DatabaseConnection()
        cursor = db.get_cursor()
        if cursor:
            try:
                cursor.execute(
                    "INSERT INTO Asiento (fila, numero, Sala_idSala) VALUES (%s, %s, %s)",
                    (self.fila, self.numero, self.id_sala)
                )
                db.commit()
                self.id_asiento = cursor.lastrowid
                return True
            except Exception as e:
                print(f"Error al guardar asiento: {e}")
                return False

    def to_dict(self):
        return {
            "idAsiento": self.id_asiento,
            "fila":      self.fila,
            "numero":    self.numero,
            "idSala":    self.id_sala
        }