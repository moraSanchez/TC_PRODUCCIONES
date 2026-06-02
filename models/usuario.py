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
            try:
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
            except Exception as e:
                print(f"Error al buscar usuario: {e}")
        return None

# --- APLICANDO HERENCIA ---
class Cliente(Usuario):
    def __init__(self, id=None, nombre=None, email=None, password=None):
        super().__init__(id, nombre, email, password, rol='cliente')
        
    def guardar(self):
        """Registra un nuevo cliente en la base de datos."""
        db = DatabaseConnection()
        cursor = db.get_cursor()
        if cursor:
            try:
                query = "INSERT INTO usuarios (nombre, email, password, rol) VALUES (%s, %s, %s, 'cliente')"
                cursor.execute(query, (self.nombre, self.email, self.password))
                db.commit()
                return True
            except Exception as e:
                print(f"Error al guardar cliente: {e}")
                return False
        return False

class Administrador(Usuario):
    def __init__(self, id=None, nombre=None, email=None, password=None):
        super().__init__(id, nombre, email, password, rol='administrador')