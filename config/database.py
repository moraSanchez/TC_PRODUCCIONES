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
                # Se añade 'port' leyendo desde las variables de entorno (por defecto 3306)
                cls._instance.connection = mysql.connector.connect(
                    host=os.getenv("DB_HOST", "localhost"),
                    user=os.getenv("DB_USER", "root"),
                    password=os.getenv("DB_PASSWORD", ""),
                    database=os.getenv("DB_NAME", "tc_producciones"),
                    port=int(os.getenv("DB_PORT", 3306)),  # <-- CORREGIDO: Ahora usa el puerto del .env
                    buffered=True  
                )
                cls._instance.cursor = cls._instance.connection.cursor(dictionary=True)
                print("Conexión Singleton a MySQL establecida con éxito.")
            except mysql.connector.Error as err:
                print(f"Error crítico de conexión a la Base de Datos: {err}")
                cls._instance.connection = None
                cls._instance.cursor = None
        return cls._instance

    def get_cursor(self):
        if self.connection and self.connection.is_connected():
            return self.cursor
        return None

    def commit(self):
        if self.connection and self.connection.is_connected():
            self.connection.commit()