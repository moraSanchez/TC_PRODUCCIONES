from config.database import DatabaseConnection

class Usuario:
    def __init__(self, id_usuario=None, nombre=None, apellido=None, email=None, contrasenia=None, tipo='Cliente'):
        self.id_usuario = id_usuario
        self.nombre = nombre
        self.apellido = apellido  # Agregamos el apellido que pide tu tabla MySQL
        self.email = email
        self.contrasenia = contrasenia
        self.tipo = tipo

    @classmethod
    def buscar_por_email(cls, email):
        """Busca un registro de forma segura usando consultas preparadas en la tabla Usuario."""
        db = DatabaseConnection()
        cursor = db.get_cursor()
        if cursor:
            try:
                # Modificado: tabla 'Usuario' y nombres de columnas de tu SQL
                cursor.execute("SELECT * FROM Usuario WHERE email = %s", (email,))
                resultado = cursor.fetchone()
                
                # NOTA: Quitamos el cursor.close() para no romper el Singleton en futuras llamadas
                if resultado:
                    return cls(
                        id_usuario=resultado['idUsuario'],
                        nombre=resultado['nombre'],
                        apellido=resultado['apellido'],
                        email=resultado['email'],
                        contrasenia=resultado['contrasenia'],
                        tipo=resultado['tipo']
                    )
            except Exception as e:
                print(f"Error en la consulta de usuarios: {e}")
        return None

    def to_dict(self):
        """Convierte el objeto a diccionario para enviarlo fácilmente como JSON a React."""
        return {
            "idUsuario": self.id_usuario,
            "nombre": self.nombre,
            "apellido": self.apellido,
            "email": self.email,
            "tipo": self.tipo
        }

# --- HERENCIA ---
class Cliente(Usuario):
    def __init__(self, id_usuario=None, nombre=None, apellido=None, email=None, contrasenia=None):
        # El tipo se asigna automáticamente como 'Cliente' en tu ENUM de MySQL
        super().__init__(id_usuario, nombre, apellido, email, contrasenia, tipo='Cliente')
        
    def guardar(self):
        """Persiste el objeto Cliente en la base de datos relacional TC_PRODUCCIONES."""
        db = DatabaseConnection()
        cursor = db.get_cursor()
        if cursor:
            try:
                # Modificado: Usamos las columnas exactas de tu esquema SQL
                query = """
                    INSERT INTO Usuario (nombre, apellido, email, contrasenia, tipo) 
                    VALUES (%s, %s, %s, %s, 'Cliente')
                """
                cursor.execute(query, (self.nombre, self.apellido, self.email, self.contrasenia))
                db.commit() # Confirmación requerida por MySQL
                
                # Obtener el ID asignado automáticamente por el AUTO_INCREMENT
                self.id_usuario = cursor.lastrowid
                return True
            except Exception as e:
                print(f"Error al persistir el Cliente: {e}")
                return False
        return False

class Administrador(Usuario):
    def __init__(self, id_usuario=None, nombre=None, apellido=None, email=None, contrasenia=None):
        super().__init__(id_usuario, nombre, apellido, email, contrasenia, tipo='Administrador')
        
    def guardar(self):
        """Persiste el objeto Administrador en la base de datos."""
        db = DatabaseConnection()
        cursor = db.get_cursor()
        if cursor:
            try:
                query = """
                    INSERT INTO Usuario (nombre, apellido, email, contrasenia, tipo) 
                    VALUES (%s, %s, %s, %s, 'Administrador')
                """
                cursor.execute(query, (self.nombre, self.apellido, self.email, self.contrasenia))
                db.commit()
                self.id_usuario = cursor.lastrowid
                return True
            except Exception as e:
                print(f"Error al persistir el Administrador: {e}")
                return False
        return False