from flask import Flask, render_template, request, redirect, url_for, flash, session
import os
from dotenv import load_dotenv

# Importamos la conexión Singleton y los Modelos OO
from config.database import DatabaseConnection
from models.usuario import Usuario, Cliente

# Cargamos el entorno (.env)
load_dotenv()

app = Flask(__name__, 
            template_folder='views/templates', 
            static_folder='views/static')

app.secret_key = os.getenv('FLASK_SECRET_KEY', 'clave_secreta_super_segura_cine')

# Instanciamos la base de datos para asegurar que intente conectar al iniciar
db = DatabaseConnection()
db.connect()

# ==========================================
# CONTROLADORES / RUTAS
# ==========================================

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        nombre = request.form.get('nombre')
        email = request.form.get('email')
        password = request.form.get('password')

        # Comprobamos si el email ya existe
        if Usuario.buscar_por_email(email):
            flash('Ese correo electrónico ya está registrado.', 'danger')
            return redirect(url_for('registro'))

        # Instanciamos la clase hija 'Cliente' (Polimorfismo/Herencia)
        nuevo_cliente = Cliente(nombre=nombre, email=email, password=password)
        
        if nuevo_cliente.guardar():
            flash('¡Registro exitoso guardado en MySQL! Ya podés ingresar.', 'success')
            return redirect(url_for('login'))
        else:
            flash('Error al guardar en la Base de Datos. Revisá tu consola.', 'danger')
            return redirect(url_for('registro'))

    return render_template('registro.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'usuario_id' in session:
        return redirect(url_for('index'))

    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        usuario = Usuario.buscar_por_email(email)

        if usuario and usuario.password == password:
            session['usuario_id'] = usuario.id
            session['usuario_nombre'] = usuario.nombre
            session['usuario_rol'] = usuario.rol
            flash(f'¡Hola de nuevo, {usuario.nombre}!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Credenciales incorrectas.', 'danger')
            return redirect(url_for('login'))

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    flash('Sesión cerrada.', 'info')
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True, port=5000)