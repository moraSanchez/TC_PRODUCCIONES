import mysql.connector
import os
from dotenv import load_dotenv

# Cargamos las variables de entorno desde el archivo .env
load_dotenv()

class DatabaseConnection:
    _instance = None  # Aquí se guardará la única instancia de la conexión (Singleton)

    def __new__(cls):
        # Si la instancia no existe, la creamos por primera y única vez
        if cls._instance is None:
            cls._instance = super(DatabaseConnection, cls).__new__(cls)
            cls._instance._connection = None
        return cls._instance

    def connect(self):
        """Establece la conexión con la base de datos si no existe una activa."""
        if self._connection is None or not self._connection.is_connected():
            try:
                self._connection = mysql.connector.connect(
                    host=os.getenv('DB_HOST'),
                    user=os.getenv('DB_USER'),
                    password=os.getenv('DB_PASSWORD'),
                    database=os.getenv('DB_NAME'),
                    port=int(os.getenv('DB_PORT', 3306))
                )
                print("¡Conexión exitosa a la base de datos de TC_PRODUCCIONES!")
            except mysql.connector.Error as err:
                print(error=f"Error al conectar a MySQL: {err}")
                self._connection = None
        return self._connection

    def get_cursor(self):
        """Devuelve un cursor para ejecutar consultas SQL."""
        connection = self.connect()
        if connection:
            # dictionary=True hace que los resultados nos lleguen como diccionarios, ideal para Flask
            return connection.cursor(dictionary=True)
        return None

    def close_connection(self):
        """Cierra la conexión de manera segura."""
        if self._connection and self._connection.is_connected():
            self._connection.close()
            print("Conexión a la base de datos cerrada de forma segura.")