from werkzeug.security import generate_password_hash, check_password_hash
from models.usuario import Usuario, Cliente

class AuthController:
    
    @staticmethod
    def registrar_usuario(nombre, apellido, email, contrasenia):
        # 1. Validar si el correo ya existe
        usuario_existente = Usuario.buscar_por_email(email)
        if usuario_existente:
            return {"error": "El correo ya está registrado"}, 400
            
        # 2. Encriptar contraseña con el tamaño completo correcto
        password_encriptada = generate_password_hash(contrasenia)
        
        # 3. Crear instancia de Cliente
        nuevo_cliente = Cliente(
            nombre=nombre, 
            apellido=apellido, 
            email=email, 
            contrasenia=password_encriptada
        )
        
        # 4. Guardar en la base de datos
        if nuevo_cliente.guardar():
            return {"mensaje": "Usuario registrado con éxito"}, 201
        else:
            return {"error": "Error interno en el servidor al guardar el usuario"}, 500

    @staticmethod
    def iniciar_sesion(email, contrasenia):
        # 1. Buscar al usuario por su email
        usuario = Usuario.buscar_por_email(email)
        
        if not usuario:
            return {"error": "Correo o contraseña incorrectos"}, 401
            
        # 2. Verificar la contraseña de forma directa usando la propiedad del objeto
        if not check_password_hash(usuario.contrasenia, contrasenia):
            return {"error": "Correo o contraseña incorrectos"}, 401
            
        # 3. Login exitoso: Devolver los datos del usuario mapeados a diccionario
        return {
            "mensaje": "Login exitoso",
            "usuario": usuario.to_dict()
        }, 200