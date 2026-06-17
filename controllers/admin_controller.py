# controllers/admin_controller.py
from models.administrador import Administrador

class AdminController:
    
    @staticmethod
    def gestionar_alta_funcion(fecha, hora, id_pelicula, id_sala):
        # Simulamos una acción ejecutada por el rol admin
        admin_maestro = Administrador(nombre="Alan", email="admin@cine.com")
        return admin_maestro.programar_funcion(fecha, hora, id_pelicula, id_sala)