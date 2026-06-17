CREATE DATABASE IF NOT EXISTS tc_producciones;
USE tc_producciones;

CREATE TABLE IF NOT EXISTS Usuario (
    idUsuario INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    apellido VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    contrasenia VARCHAR(255) NOT NULL,
    tipo ENUM('Administrador', 'Cliente') NOT NULL DEFAULT 'Cliente',
    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS Pelicula (
    idPelicula INT AUTO_INCREMENT PRIMARY KEY,
    titulo VARCHAR(150) NOT NULL,
    sinopsis TEXT,
    duracion INT,
    genero VARCHAR(50),
    imagen_url VARCHAR(255)
);

CREATE TABLE IF NOT EXISTS Sala (
    idSala INT AUTO_INCREMENT PRIMARY KEY,
    numero INT NOT NULL,
    capacidad INT NOT NULL
);

CREATE TABLE IF NOT EXISTS Asiento (
    idAsiento INT AUTO_INCREMENT PRIMARY KEY,
    fila CHAR(1) NOT NULL,
    numero INT NOT NULL,
    Sala_idSala INT NOT NULL,
    FOREIGN KEY (Sala_idSala) REFERENCES Sala(idSala) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS Funcion (
    idFuncion INT AUTO_INCREMENT PRIMARY KEY,
    fecha DATE NOT NULL,
    hora TIME NOT NULL,
    estado VARCHAR(50) DEFAULT 'activa',
    Pelicula_idPelicula INT NOT NULL,
    Sala_idSala INT NOT NULL,
    FOREIGN KEY (Pelicula_idPelicula) REFERENCES Pelicula(idPelicula),
    FOREIGN KEY (Sala_idSala) REFERENCES Sala(idSala)
);

CREATE TABLE IF NOT EXISTS Reserva (
    idReserva INT AUTO_INCREMENT PRIMARY KEY,
    fecha DATE NOT NULL,
    estado VARCHAR(50) DEFAULT 'pendiente',
    Usuario_idUsuario INT NOT NULL,
    Funcion_idFuncion INT NOT NULL,
    FOREIGN KEY (Usuario_idUsuario) REFERENCES Usuario(idUsuario),
    FOREIGN KEY (Funcion_idFuncion) REFERENCES Funcion(idFuncion)
);

CREATE TABLE IF NOT EXISTS ReservaAsiento (
    idReservaAsiento INT AUTO_INCREMENT PRIMARY KEY,
    Reserva_idReserva INT NOT NULL,
    Asiento_idAsiento INT NOT NULL,
    precio DECIMAL(10,2) NOT NULL,
    estado VARCHAR(50) DEFAULT 'reservado',
    FOREIGN KEY (Reserva_idReserva) REFERENCES Reserva(idReserva),
    FOREIGN KEY (Asiento_idAsiento) REFERENCES Asiento(idAsiento)
);

CREATE TABLE IF NOT EXISTS Ticket (
    idTicket INT AUTO_INCREMENT PRIMARY KEY,
    codigo VARCHAR(12) NOT NULL UNIQUE,
    fecha DATE NOT NULL,
    Reserva_idReserva INT NOT NULL,
    FOREIGN KEY (Reserva_idReserva) REFERENCES Reserva(idReserva)
);

CREATE TABLE IF NOT EXISTS Pago (
    idPago INT AUTO_INCREMENT PRIMARY KEY,
    metodo VARCHAR(50) NOT NULL,
    estado VARCHAR(50) NOT NULL,
    Reserva_idReserva INT NOT NULL,
    FOREIGN KEY (Reserva_idReserva) REFERENCES Reserva(idReserva)
);