-- =====================================================================
-- SCRIPT COMPLETO DE BASE DE DATOS: tc_producciones
-- =====================================================================

DROP DATABASE IF EXISTS tc_producciones;
CREATE DATABASE tc_producciones CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE tc_producciones;

-- 1. Tabla: Usuario
CREATE TABLE Usuario (
    idUsuario INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    apellido VARCHAR(100),
    email VARCHAR(150) NOT NULL UNIQUE,
    contrasenia VARCHAR(255) NOT NULL, -- Ampliado a 255 para soportar los hashes de Werkzeug/scrypt
    tipo VARCHAR(50) DEFAULT 'Cliente' NOT NULL
) ENGINE=InnoDB;

-- 2. Tabla: Pelicula
CREATE TABLE Pelicula (
    idPelicula INT AUTO_INCREMENT PRIMARY KEY,
    titulo VARCHAR(200) NOT NULL,
    sinopsis TEXT,
    duracion INT DEFAULT 120,
    genero VARCHAR(100),
    imagen_url TEXT
) ENGINE=InnoDB;

-- 3. Tabla: Sala
CREATE TABLE Sala (
    idSala INT PRIMARY KEY,
    nombre VARCHAR(50) NOT NULL,
    capacidad INT DEFAULT 60
) ENGINE=InnoDB;

-- Inserción por defecto de salas básicas
INSERT INTO Sala (idSala, nombre, capacidad) VALUES 
(1, 'Sala General 1', 60),
(2, 'Sala General 2', 60),
(3, 'Sala 3D Max', 45),
(4, 'Sala VIP', 30);

-- 4. Tabla: Funcion (Estructura Relacional Limpia y Corregida)
CREATE TABLE Funcion (
    idFuncion INT AUTO_INCREMENT PRIMARY KEY,
    Sala_idSala INT NOT NULL,
    Pelicula_idPelicula INT NOT NULL,
    fecha DATE NOT NULL,
    hora TIME NOT NULL,
    estado VARCHAR(50) DEFAULT 'activa' NOT NULL, -- Garantiza que 'activa' no quede NULL
    idioma VARCHAR(50) DEFAULT 'Doblada',
    formato VARCHAR(20) DEFAULT '2D',
    FOREIGN KEY (Sala_idSala) REFERENCES Sala(idSala) ON DELETE CASCADE,
    FOREIGN KEY (Pelicula_idPelicula) REFERENCES Pelicula(idPelicula) ON DELETE CASCADE
) ENGINE=InnoDB;

-- 5. Tabla: Asiento
CREATE TABLE Asiento (
    idAsiento INT AUTO_INCREMENT PRIMARY KEY,
    Sala_idSala INT NOT NULL,
    fila CHAR(1) NOT NULL,
    numero INT NOT NULL,
    FOREIGN KEY (Sala_idSala) REFERENCES Sala(idSala) ON DELETE CASCADE
) ENGINE=InnoDB;

-- 6. Tabla: Reserva
CREATE TABLE Reserva (
    idReserva INT AUTO_INCREMENT PRIMARY KEY,
    Usuario_idUsuario INT NOT NULL,
    Funcion_idFuncion INT NOT NULL,
    fecha_reserva DATETIME DEFAULT CURRENT_TIMESTAMP,
    total DECIMAL(10, 2) NOT NULL,
    estado_pago VARCHAR(50) DEFAULT 'pendiente',
    mercadopago_preference_id VARCHAR(255),
    FOREIGN KEY (Usuario_idUsuario) REFERENCES Usuario(idUsuario) ON DELETE CASCADE,
    FOREIGN KEY (Funcion_idFuncion) REFERENCES Funcion(idFuncion) ON DELETE CASCADE
) ENGINE=InnoDB;

-- 7. Tabla: ReservaAsiento (Tabla intermedia para ocupación de butacas)
CREATE TABLE ReservaAsiento (
    Reserva_idReserva INT NOT NULL,
    Asiento_idAsiento INT NOT NULL,
    PRIMARY KEY (Reserva_idReserva, Asiento_idAsiento),
    FOREIGN KEY (Reserva_idReserva) REFERENCES Reserva(idReserva) ON DELETE CASCADE,
    FOREIGN KEY (Asiento_idAsiento) REFERENCES Asiento(idAsiento) ON DELETE CASCADE
) ENGINE=InnoDB;

-- 8. Tabla: Entrada (Precios por formato de función: 2D, 3D, 4D, XD)  -- ★ NUEVA
CREATE TABLE Entrada (
    id_entrada VARCHAR(20) PRIMARY KEY, -- Coincide con el campo 'formato' de la tabla Funcion
    precio DECIMAL(10,2) NOT NULL
) ENGINE=InnoDB;

-- Precios iniciales por formato  -- ★ NUEVO
INSERT INTO Entrada (id_entrada, precio) VALUES
('2D', 4500.00),
('3D', 5500.00),
('4D', 7000.00),
('XD', 6500.00);

-- =====================================================================
-- INSERCIÓN DE USUARIO ADMINISTRADOR DE PRUEBA
-- =====================================================================
-- Nota: La contraseña 'admin123' está hardcodeada temporalmente como fallback en tu auth_controller.py
INSERT INTO Usuario (nombre, apellido, email, contrasenia, tipo) 
VALUES ('Admin', 'Cine', 'admin@cine.com', 'admin123', 'Administrador');

-- =====================================================================
-- VERIFICACIÓN FINAL
-- =====================================================================
SHOW TABLES;