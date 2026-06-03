from werkzeug.security import generate_password_hash, check_password_hash
from models.usuario import Usuario, Cliente

class AuthController:
    
    @staticmethod
    def registrar_usuario(nombre, apellido, email, contrasenia):
        # 1. Buscar si el email ya existe usando el método de clase del modelo Usuario
        usuario_existente = Usuario.buscar_por_email(email)
        if usuario_existente:
            return {"error": "El correo ya está registrado"}, 400
            
        # 2. Encriptar la contraseña de forma segura
        password_encriptada = generate_password_hash(contrasenia)
        
        # 3. Instanciar la clase Cliente (que hereda de Usuario y setea el tipo 'Cliente')
        nuevo_cliente = Cliente(
            nombre=nombre, 
            apellido=apellido, 
            email=email, 
            contrasenia=password_encriptada
        )
        
        # 4. Llamar al método guardar que definiste en tu modelo
        if nuevo_cliente.guardar():
            return {"mensaje": "Usuario registrado con éxito"}, 201
        else:
            return {"error": "Error interno en el servidor al guardar el usuario"}, 500

    @staticmethod
    def iniciar_sesion(email, contrasenia):
        # 1. Buscar al usuario usando el método estático/clase del modelo
        usuario = Usuario.buscar_por_email(email)
        
        if not usuario:
            return {"error": "Correo o contraseña incorrectos"}, 401
            
        # 2. Verificar la contraseña encriptada usando el atributo del objeto recuperado
        if not check_password_hash(usuario.contrasenia, contrasenia):
            return {"error": "Correo o contraseña incorrectos"}, 401
            
        # 3. Retornar los datos convirtiendo el objeto en diccionario gracias a tu método .to_dict()
        return {
            "mensaje": "Login exitoso",
            "usuario": usuario.to_dict()
        }, 200