#usuario.py

from config.database import DatabaseConnection

class Usuario:
    def __init__(self, id_usuario=None, nombre=None, apellido=None, email=None, contrasenia=None, tipo='Cliente'):
        self.id_usuario = id_usuario
        self.nombre = nombre
        self.apellido = apellido
        self.email = email
        self.contrasenia = contrasenia
        self.tipo = tipo

    @classmethod
    def buscar_por_email(cls, email):
        db = DatabaseConnection()
        cursor = db.get_cursor()
        if cursor:
            try:
                # Nos aseguramos de leer el estado limpio del cursor antes de ejecutar
                cursor.execute("SELECT * FROM Usuario WHERE email = %s", (email,))
                resultado = cursor.fetchone()
                
                if resultado:
                    tipo_usuario = resultado.get('tipo', 'Cliente')
                    
                    if tipo_usuario == 'Administrador':
                        return Administrador(
                            id_usuario=resultado['idUsuario'],
                            nombre=resultado['nombre'],
                            apellido=resultado['apellido'],
                            email=resultado['email'],
                            contrasenia=resultado['contrasenia']
                        )
                    else:
                        return Cliente(
                            id_usuario=resultado['idUsuario'],
                            nombre=resultado['nombre'],
                            apellido=resultado['apellido'],
                            email=resultado['email'],
                            contrasenia=resultado['contrasenia']
                        )
            except Exception as e:
                print(f"Error en la consulta de usuarios: {e}")
        return None

    def to_dict(self):
        return {
            "idUsuario": self.id_usuario,
            "nombre": self.nombre,
            "apellido": self.apellido,
            "email": self.email,
            "tipo": self.tipo
        }

class Cliente(Usuario):
    def __init__(self, id_usuario=None, nombre=None, apellido=None, email=None, contrasenia=None):
        super().__init__(id_usuario, nombre, apellido, email, contrasenia, tipo='Cliente')
        
    def guardar(self):
        db = DatabaseConnection()
        cursor = db.get_cursor()
        if cursor:
            try:
                query = """
                    INSERT INTO Usuario (nombre, apellido, email, contrasenia, tipo) 
                    VALUES (%s, %s, %s, %s, 'Cliente')
                """
                cursor.execute(query, (self.nombre, self.apellido, self.email, self.contrasenia))
                db.commit()
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
