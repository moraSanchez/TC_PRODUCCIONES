-- Crear base de datos si no existe
CREATE DATABASE IF NOT EXISTS `tc_producciones` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;
USE `tc_producciones`;

-- 1. Tabla: usuario
CREATE TABLE IF NOT EXISTS `usuario` (
  `idUsuario` INT(11) NOT NULL AUTO_INCREMENT,
  `nombre` VARCHAR(100) NOT NULL,
  `apellido` VARCHAR(100) NOT NULL,
  `email` VARCHAR(150) NOT NULL UNIQUE,
  `contrasenia` VARCHAR(255) NOT NULL,
  `tipo` VARCHAR(50) NOT NULL DEFAULT 'Cliente',
  PRIMARY KEY (`idUsuario`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- 2. Tabla: pelicula
CREATE TABLE IF NOT EXISTS `pelicula` (
  `idPelicula` INT(11) NOT NULL AUTO_INCREMENT,
  `titulo` VARCHAR(150) NOT NULL,
  `sinopsis` TEXT DEFAULT NULL,
  `duracion` INT(11) NOT NULL DEFAULT 120,
  `genero` VARCHAR(100) DEFAULT NULL,
  `imagen_url` VARCHAR(255) DEFAULT NULL,
  PRIMARY KEY (`idPelicula`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- 3. Tabla: sala
CREATE TABLE IF NOT EXISTS `sala` (
  `idSala` INT(11) NOT NULL AUTO_INCREMENT,
  `num_sala` INT(11) NOT NULL,
  `capacidad` INT(11) NOT NULL DEFAULT 60,
  PRIMARY KEY (`idSala`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- Insertar salas básicas por defecto si están vacías
INSERT INTO `sala` (`idSala`, `num_sala`, `capacidad`) VALUES (1, 1, 60), (2, 2, 60), (3, 3, 60), (4, 4, 60)
ON DUPLICATE KEY UPDATE `num_sala`=`num_sala`;

-- 4. Tabla: funcion
CREATE TABLE IF NOT EXISTS `funcion` (
  `idFuncion` INT(11) NOT NULL AUTO_INCREMENT,
  `titulo` VARCHAR(150) DEFAULT NULL,
  `genero` VARCHAR(100) DEFAULT NULL,
  `imagen_url` VARCHAR(255) DEFAULT NULL,
  `num_sala` INT(11) NOT NULL DEFAULT 1,
  `fecha` DATE NOT NULL,
  `hora` TIME NOT NULL,
  `estado` VARCHAR(50) NOT NULL DEFAULT 'activa',
  `idioma` VARCHAR(50) DEFAULT 'Doblada',
  `formato` VARCHAR(50) DEFAULT 'Normal',
  `precio` DECIMAL(10,2) NOT NULL DEFAULT 4500.00,
  `Pelicula_idPelicula` INT(11) NOT NULL,
  `Sala_idSala` INT(11) NOT NULL DEFAULT 1,
  PRIMARY KEY (`idFuncion`),
  CONSTRAINT `fk_funcion_pelicula` FOREIGN KEY (`Pelicula_idPelicula`) REFERENCES `pelicula` (`idPelicula`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_funcion_sala` FOREIGN KEY (`Sala_idSala`) REFERENCES `sala` (`idSala`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- 5. Tabla: asiento
CREATE TABLE IF NOT EXISTS `asiento` (
  `idAsiento` INT(11) NOT NULL AUTO_INCREMENT,
  `fila` CHAR(1) NOT NULL,
  `numero` INT(11) NOT NULL,
  `Sala_idSala` INT(11) NOT NULL,
  PRIMARY KEY (`idAsiento`),
  CONSTRAINT `fk_asiento_sala` FOREIGN KEY (`Sala_idSala`) REFERENCES `sala` (`idSala`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- 6. Tabla: reserva
CREATE TABLE IF NOT EXISTS `reserva` (
  `idReserva` INT(11) NOT NULL AUTO_INCREMENT,
  `Usuario_idUsuario` INT(11) NOT NULL,
  `Funcion_idFuncion` INT(11) NOT NULL,
  `cantidad_butacas` INT(11) NOT NULL DEFAULT 1,
  `fecha_reserva` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`idReserva`),
  CONSTRAINT `fk_reserva_usuario` FOREIGN KEY (`Usuario_idUsuario`) REFERENCES `usuario` (`idUsuario`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_reserva_funcion` FOREIGN KEY (`Funcion_idFuncion`) REFERENCES `funcion` (`idFuncion`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- 7. Tabla: reservaasiento (Tabla intermedia)
CREATE TABLE IF NOT EXISTS `reservaasiento` (
  `Reserva_idReserva` INT(11) NOT NULL,
  `Asiento_idAsiento` INT(11) NOT NULL,
  PRIMARY KEY (`Reserva_idReserva`, `Asiento_idAsiento`),
  CONSTRAINT `fk_ra_reserva` FOREIGN KEY (`Reserva_idReserva`) REFERENCES `reserva` (`idReserva`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_ra_asiento` FOREIGN KEY (`Asiento_idAsiento`) REFERENCES `asiento` (`idAsiento`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- 8. Tabla: pago
CREATE TABLE IF NOT EXISTS `pago` (
  `idPago` INT(11) NOT NULL AUTO_INCREMENT,
  `monto` DECIMAL(10,2) NOT NULL,
  `fecha_pago` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `metodo` VARCHAR(50) NOT NULL DEFAULT 'Mercado Pago',
  `estado` VARCHAR(50) NOT NULL DEFAULT 'aprobado',
  `Reserva_idReserva` INT(11) NOT NULL,
  PRIMARY KEY (`idPago`),
  CONSTRAINT `fk_pago_reserva` FOREIGN KEY (`Reserva_idReserva`) REFERENCES `reserva` (`idReserva`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- 9. Tabla: ticket
CREATE TABLE IF NOT EXISTS `ticket` (
  `idTicket` INT(11) NOT NULL AUTO_INCREMENT,
  `codigo_unico` VARCHAR(50) NOT NULL UNIQUE,
  `Reserva_idReserva` INT(11) NOT NULL,
  PRIMARY KEY (`idTicket`),
  CONSTRAINT `fk_ticket_reserva` FOREIGN KEY (`Reserva_idReserva`) REFERENCES `reserva` (`idReserva`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;