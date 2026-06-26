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

    @classmethod
    def buscar_o_crear_por_google(cls, email, nombre, apellido, google_id):
        """
        Busca un usuario por su google_id o email. Si no existe, crea un
        Cliente nuevo vinculado a esa cuenta de Google (sin contraseña local).
        Retorna una instancia de Cliente o Administrador, o None si falla.
        """
        from models.cliente import Cliente
        from models.administrador import Administrador

        db = DatabaseConnection()
        cursor = db.get_cursor()
        if not cursor:
            return None

        try:
            cursor.execute(
                "SELECT * FROM Usuario WHERE google_id = %s OR LOWER(email) = LOWER(%s)",
                (google_id, email)
            )
            resultado = cursor.fetchone()

            if resultado:
                if not resultado.get('google_id'):
                    cursor.execute(
                        "UPDATE Usuario SET google_id = %s WHERE idUsuario = %s",
                        (google_id, resultado['idUsuario'])
                    )
                    db.commit()
                id_usuario = resultado['idUsuario']
                tipo = resultado.get('tipo', 'Cliente')
                nombre_final = resultado['nombre']
                apellido_final = resultado.get('apellido')
            else:
                cursor.execute(
                    """INSERT INTO Usuario (nombre, apellido, email, contrasenia, tipo, google_id)
                    VALUES (%s, %s, %s, %s, 'Cliente', %s)""",
                    (nombre, apellido, email, None, google_id)
                )
                db.commit()
                id_usuario = cursor.lastrowid
                tipo = 'Cliente'
                nombre_final = nombre
                apellido_final = apellido

            cursor.close()

            if tipo == 'Administrador':
                return Administrador(id_usuario=id_usuario, nombre=nombre_final, apellido=apellido_final, email=email)
            return Cliente(id_usuario=id_usuario, nombre=nombre_final, apellido=apellido_final, email=email)

        except Exception as e:
            print(f"Error en buscar_o_crear_por_google: {e}")
            cursor.close()
            return None

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
