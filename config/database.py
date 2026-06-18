import mysql.connector
import os
from dotenv import load_dotenv

load_dotenv()

class DatabaseConnection:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatabaseConnection, cls).__new__(cls)
            try:
                cls._instance.connection = mysql.connector.connect(
                    host=os.getenv("DB_HOST", "localhost"),
                    user=os.getenv("DB_USER", "root"),
                    password=os.getenv("DB_PASSWORD", ""),
                    database=os.getenv("DB_NAME", "tc_producciones"),
                    buffered=True  
                )
                cls._instance.cursor = cls._instance.connection.cursor(dictionary=True)
                print("Conexión Singleton a MySQL establecida con éxito.")
            except mysql.connector.Error as err:
                print(f"Error de conexión: {err}")
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