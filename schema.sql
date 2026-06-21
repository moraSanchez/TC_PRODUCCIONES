CREATE DATABASE IF NOT EXISTS tc_producciones;
USE tc_producciones;

-- 1. Tabla Usuario
CREATE TABLE IF NOT EXISTS Usuario (
    idUsuario INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    apellido VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    contrasenia VARCHAR(255) NOT NULL,
    tipo ENUM('Administrador', 'Cliente') NOT NULL DEFAULT 'Cliente',
    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Tabla Pelicula
CREATE TABLE IF NOT EXISTS Pelicula (
    idPelicula INT AUTO_INCREMENT PRIMARY KEY,
    titulo VARCHAR(150) NOT NULL,
    sinopsis TEXT,
    duracion INT,
    genero VARCHAR(50),
    imagen_url VARCHAR(255)
);

-- 3. Tabla Sala (Se agrega capacidad por defecto)
CREATE TABLE IF NOT EXISTS Sala (
    idSala INT AUTO_INCREMENT PRIMARY KEY,
    numero INT NOT NULL,
    capacidad INT NOT NULL DEFAULT 50 -- <- Todas tendrán 50 por defecto si no se especifica
);

-- 4. Tabla Asiento
CREATE TABLE IF NOT EXISTS Asiento (
    idAsiento INT AUTO_INCREMENT PRIMARY KEY,
    fila CHAR(1) NOT NULL,
    numero INT NOT NULL,
    Sala_idSala INT NOT NULL,
    FOREIGN KEY (Sala_idSala) REFERENCES Sala(idSala) ON DELETE CASCADE
);

-- 5. Tabla Funcion
CREATE TABLE IF NOT EXISTS Funcion (
    idFuncion INT AUTO_INCREMENT PRIMARY KEY,
    titulo VARCHAR(150) NOT NULL,
    genero VARCHAR(100),
    imagen_url VARCHAR(255),
    num_sala INT NOT NULL,
    fecha DATE NOT NULL,
    hora TIME NOT NULL,
    estado VARCHAR(50) DEFAULT 'activa',
    idioma VARCHAR(50) DEFAULT 'Doblada',
    Pelicula_idPelicula INT NULL,
    Sala_idSala INT NULL,
    FOREIGN KEY (Pelicula_idPelicula) REFERENCES Pelicula(idPelicula),
    FOREIGN KEY (Sala_idSala) REFERENCES Sala(idSala)
);

-- 6. Tabla Reserva
CREATE TABLE IF NOT EXISTS Reserva (
    idReserva INT AUTO_INCREMENT PRIMARY KEY,
    fecha DATE NOT NULL,
    estado VARCHAR(50) DEFAULT 'pendiente',
    Usuario_idUsuario INT NOT NULL,
    Funcion_idFuncion INT NOT NULL,
    FOREIGN KEY (Usuario_idUsuario) REFERENCES Usuario(idUsuario),
    FOREIGN KEY (Funcion_idFuncion) REFERENCES Funcion(idFuncion)
);

-- 7. Tabla ReservaAsiento
CREATE TABLE IF NOT EXISTS ReservaAsiento (
    idReservaAsiento INT AUTO_INCREMENT PRIMARY KEY,
    Reserva_idReserva INT NOT NULL,
    Asiento_idAsiento INT NOT NULL,
    precio DECIMAL(10,2) NOT NULL,
    estado VARCHAR(50) DEFAULT 'reservado',
    FOREIGN KEY (Reserva_idReserva) REFERENCES Reserva(idReserva),
    FOREIGN KEY (Asiento_idAsiento) REFERENCES Asiento(idAsiento)
);

-- 8. Tabla Ticket
CREATE TABLE IF NOT EXISTS Ticket (
    idTicket INT AUTO_INCREMENT PRIMARY KEY,
    codigo VARCHAR(12) NOT NULL UNIQUE,
    fecha DATE NOT NULL,
    Reserva_idReserva INT NOT NULL,
    FOREIGN KEY (Reserva_idReserva) REFERENCES Reserva(idReserva)
);

-- 9. Tabla Pago
CREATE TABLE IF NOT EXISTS Pago (
    idPago INT AUTO_INCREMENT PRIMARY KEY,
    metodo VARCHAR(50) NOT NULL,
    estado VARCHAR(50) NOT NULL,
    Reserva_idReserva INT NOT NULL,
    FOREIGN KEY (Reserva_idReserva) REFERENCES Reserva(idReserva)
);

-- INSERTS DE DATOS OBLIGATORIOS Y DE PRUEBA
INSERT INTO Usuario (nombre, apellido, email, contrasenia, tipo) 
VALUES ('Alan', 'Admin', 'admin@cine.com', 'scrypt:32768:8:1$v39rX6H87WpZEnZk$9fa07f877fca99d5f7c320d39e55b1bf8df8bf0600bce4cf4b5fde540f25ceb1ba420d43f01b3b2da22572b918b958c2b53569421df89cba00b740523e43db62', 'Administrador')
ON DUPLICATE KEY UPDATE tipo='Administrador';

INSERT IGNORE INTO Pelicula (idPelicula, titulo, sinopsis, duracion, genero, imagen_url) VALUES 
(1, 'Avengers: Endgame', 'Los Vengadores se reúnen para deshacer el daño de Thanos.', 181, 'Acción / Ciencia Ficción', 'avengers.jpg'),
(2, 'Interstellar', 'Un grupo de científicos viaja al espacio exterior para salvar a la humanidad.', 169, 'Drama / Sci-Fi', 'interstellar.jpg'),
(3, 'El Padrino', 'La vida de una organización criminal y su transición generacional.', 175, 'Crimen / Drama', 'padrino.jpg');

-- CORRECCIÓN: Todas las salas ahora se insertan con capacidad 50
INSERT IGNORE INTO Sala (idSala, numero, capacidad) VALUES 
(1, 1, 50),
(2, 2, 50),
(3, 3, 50),
(4, 4, 50),
(5, 5, 50),
(6, 6, 50);