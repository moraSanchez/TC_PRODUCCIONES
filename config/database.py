import mysql.connector
import os
from dotenv import load_dotenv

# Cargar las variables de entorno desde el archivo .env
load_dotenv()

class DatabaseConnection:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatabaseConnection, cls).__new__(cls)
            try:
                # Mantiene la conexión única como propiedad global del Singleton
                cls._instance.connection = mysql.connector.connect(
                    host=os.getenv("DB_HOST", "localhost"),
                    user=os.getenv("DB_USER", "root"),
                    password=os.getenv("DB_PASSWORD", ""),
                    database=os.getenv("DB_NAME", "tc_producciones"),
                    port=int(os.getenv("DB_PORT", 3306)),
                    buffered=True  
                )
                print("Conexión Singleton a MySQL establecida con éxito.")
            except mysql.connector.Error as err:
                print(f"Error crítico de conexión a la Base de Datos: {err}")
                cls._instance.connection = None
        return cls._instance

    def get_cursor(self):
        """
        Genera un cursor limpio por cada petición web para evitar que los hilos
        y bucles de inserción concurrentes colisionen entre sí.
        """
        try:
            if self.connection and self.connection.is_connected():
                return self.connection.cursor(dictionary=True)
        except Exception as e:
            print(f"❌ Error al generar cursor dinámico: {e}")
        return None

    def commit(self):
        if self.connection and self.connection.is_connected():
            self.connection.commit()