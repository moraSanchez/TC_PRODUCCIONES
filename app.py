from flask import Flask, render_template, request, redirect, url_for, flash, session
import os
from dotenv import load_dotenv

# Importamos nuestro Singleton de la base de datos y los Modelos
from config.database import DatabaseConnection
from models.usuario import Usuario, Cliente, Administrador

# Cargamos las variables de entorno del archivo .env
load_dotenv()

# Inicializamos Flask y le indicamos las rutas de las carpetas de diseño
app = Flask(__name__, 
            template_folder='views/templates', 
            static_folder='views/static')

# Clave secreta necesaria para manejar sesiones y mensajes "flash" en pantalla
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'clave_secreta_por_defecto_cine')


# =========================================================================
# RUTAS DEL SISTEMA (CONTROLADORES)
# =========================================================================

@app.route('/')
def index():
    """Ruta de la pantalla de inicio."""
    # Obtenemos los datos del usuario si ya inició sesión
    usuario_actual = session.get('usuario')
    return render_template('index.html', usuario=usuario_actual)


@app.route('/login', methods=['GET', 'POST'])
def login():
    """Ruta para el inicio de sesión."""
    # Si el usuario ya está logueado, lo mandamos al inicio
    if 'usuario_id' in session:
        return redirect(url_for('index'))

    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        # Buscamos al usuario en la Base de Datos usando el método de la clase
        usuario = Usuario.buscar_por_email(email)

        if usuario and usuario.password == password:  
            # 💡 Nota: En producción las contraseñas se encriptan, pero para la facu así está perfecto.
            
            # Guardamos los datos clave en la sesión del navegador
            session['usuario_id'] = usuario.id
            session['usuario_nombre'] = usuario.nombre
            session['usuario_rol'] = usuario.rol

            flash(f'¡Bienvenido/a de nuevo, {usuario.nombre}!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Correo electrónico o contraseña incorrectos.', 'danger')
            return redirect(url_for('login'))

    # Si entra por GET (normal), le mostramos el formulario
    return render_template('login.html')


@app.route('/logout')
def logout():
    """Ruta para cerrar sesión y limpiar el navegador."""
    session.clear()
    flash('Cerraste sesión correctamente.', 'info')
    return redirect(url_for('index'))


# =========================================================================
# CONTROL DE ERRORES (Para que la app no tire una pantalla blanca fea)
# =========================================================================

@app.errorhandler(404)
def page_not_found(e):
    return "<h3>Error 404: La página que buscás no existe en TC_PRODUCCIONES.</h3>", 404


# Arranque del servidor local
if __name__ == '__main__':
    # debug=True hace que el servidor se reinicie solo cada vez que guardás un cambio
    app.run(debug=True, port=5000)