#administrador.py

from models.usuario import Usuario
from models.funcion import Funcion

class Administrador(Usuario):
    def __init__(self, id_usuario=None, nombre=None, apellido=None, email=None, contrasenia=None):
        # Invocamos al constructor de la clase padre (Usuario)
        super().__init__(id_usuario, nombre, apellido, email, contrasenia, tipo='Administrador')

    def programar_funcion(self, fecha, hora, id_pelicula, id_sala):
        """Mapea la capacidad del administrador de dar de alta una función"""
        nueva_funcion = Funcion(fecha=fecha, hora=hora, id_pelicula=id_pelicula, id_sala=id_sala)
        return nueva_funcion.guardar()

    def cancelar_funcion(self, id_funcion):
        """Mapea la capacidad del administrador de dar de baja una función"""
        funcion_a_eliminar = Funcion(id_funcion=id_funcion)
        return funcion_a_eliminar.eliminar()