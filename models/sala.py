from config.database import DatabaseConnection
from models.asiento import Asiento

FILAS = ['A','B','C','D','E','F','G','H']

class Sala:
    """
    COMPOSICIÓN: Sala es responsable del ciclo de vida de sus Asientos.
    Si se elimina la sala, los asientos se eliminan (ON DELETE CASCADE).
    """
    def __init__(self, id_sala=None, numero=None, capacidad=None):
        self.id_sala    = id_sala
        self.numero     = numero
        self.capacidad  = capacidad
        self.asientos   = []  # Composición: parte de Sala

    def guardar(self):
        db = DatabaseConnection()
        cursor = db.get_cursor()
        if cursor:
            try:
                cursor.execute(
                    "INSERT INTO Sala (numero, capacidad) VALUES (%s, %s)",
                    (self.numero, self.capacidad)
                )
                db.commit()
                self.id_sala = cursor.lastrowid
                self._crear_asientos()
                return True
            except Exception as e:
                print(f"Error al guardar sala: {e}")
                return False

    def _crear_asientos(self):
        """Composición: la Sala crea y gestiona sus Asientos."""
        asientos_por_fila = self.capacidad // len(FILAS)
        for fila in FILAS:
            for num in range(1, asientos_por_fila + 1):
                asiento = Asiento(fila=fila, numero=num, id_sala=self.id_sala)
                asiento.guardar()
                self.asientos.append(asiento)

    @classmethod
    def buscar_por_id(cls, id_sala):
        db = DatabaseConnection()
        cursor = db.get_cursor()
        if cursor:
            cursor.execute("SELECT * FROM Sala WHERE idSala = %s", (id_sala,))
            r = cursor.fetchone()
            if r:
                return cls(id_sala=r['idSala'], numero=r['numero'], capacidad=r['capacidad'])
        return None