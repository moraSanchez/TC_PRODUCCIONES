from config.database import DatabaseConnection

class Usuario:
    def __init__(self, id=None, nombre=None, email=None, password=None, rol=None):
        self.id = id
        self.nombre = nombre
        self.email = email
        self.password = password
        self.rol = rol

    @classmethod
    def buscar_por_email(cls, email):
        """Busca un usuario en la BD por su email."""
        db = DatabaseConnection()
        cursor = db.get_cursor()
        if cursor:
            cursor.execute("SELECT * FROM usuarios WHERE email = %s", (email,))
            resultado = cursor.fetchone()
            if resultado:
                return cls(
                    id=resultado['id'],
                    nombre=resultado['nombre'],
                    email=resultado['email'],
                    password=resultado['password'],
                    rol=resultado['rol']
                )
        return None

# --- APLICANDO HERENCIA ---
class Cliente(Usuario):
    def __init__(self, id=None, nombre=None, email=None, password=None):
        # Invocamos al constructor de la clase madre pasando el rol fijo
        super().__init__(id, nombre, email, password, rol='cliente')
        
    def guardar(self):
        """Registra un nuevo cliente en la base de datos."""
        db = DatabaseConnection()
        conexion = db.connect()
        cursor = db.get_cursor()
        if cursor:
            query = "INSERT INTO usuarios (nombre, email, password, rol) VALUES (%s, %s, %s, 'cliente')"
            cursor.execute(query, (self.nombre, self.email, self.password))
            conexion.commit()
            return True
        return False

class Administrador(Usuario):
    def __init__(self, id=None, nombre=None, email=None, password=None):
        super().__init__(id, nombre, email, password, rol='administrador')
        
    def registrar_pelicula(self, titulo, sinopsis, duracion, genero):
        """Método exclusivo del administrador para agregar películas."""
        db = DatabaseConnection()
        conexion = db.connect()
        cursor = db.get_cursor()
        if cursor:
            query = "INSERT INTO peliculas (titulo, sinopsis, duracion, genero) VALUES (%s, %s, %s, %s)"
            cursor.execute(query, (titulo, sinopsis, duracion, genero))
            conexion.commit()
            return True
        return False