# models/pelicula.py
from config.database import DatabaseConnection

class Pelicula:
    def __init__(self, id_pelicula=None, titulo=None, duracion=None, genero=None, clasificacion=None, imagen_url=None):
        self.id_pelicula = id_pelicula
        self.titulo = titulo
        self.duracion = duracion
        self.genero = genero
        self.clasificacion = clasificacion
        self.imagen_url = imagen_url

    @classmethod
    def buscar_por_id(cls, id_pelicula):
        db = DatabaseConnection()
        cursor = db.get_cursor()
        if cursor:
            cursor.execute("SELECT * FROM Pelicula WHERE idPelicula = %s", (id_pelicula,))
            r = cursor.fetchone()
            if r:
                return cls(
                    id_pelicula=r['idPelicula'], 
                    titulo=r['titulo'], 
                    duracion=r['duracion'], 
                    genero=r['genero'], 
                    clasificacion=r['clasificacion'],
                    imagen_url=r.get('imagen_url')
                )
        return None