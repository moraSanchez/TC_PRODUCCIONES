SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

-- --------------------------------------------------------
-- 1. SELECCIÓN Y CREACIÓN AUTOMÁTICA DE LA BASE DE DATOS
-- --------------------------------------------------------
CREATE DATABASE IF NOT EXISTS `tc_producciones` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;
USE `tc_producciones`;

-- --------------------------------------------------------
-- 2. ESTRUCTURA DE LAS TABLAS
-- --------------------------------------------------------

CREATE TABLE `asiento` (
  `idAsiento` int(11) NOT NULL,
  `fila` char(1) NOT NULL,
  `numero` int(11) NOT NULL,
  `Sala_idSala` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

CREATE TABLE `funcion` (
  `idFuncion` int(11) NOT NULL,
  `titulo` varchar(150) NOT NULL,
  `genero` varchar(100) DEFAULT NULL,
  `imagen_url` varchar(255) DEFAULT NULL,
  `num_sala` int(11) NOT NULL,
  `fecha` date NOT NULL,
  `hora` time NOT NULL,
  `estado` varchar(50) DEFAULT 'activa',
  `idioma` varchar(50) DEFAULT 'Doblada',
  `Pelicula_idPelicula` int(11) DEFAULT NULL,
  `Sala_idSala` int(11) DEFAULT NULL,
  `formato` varchar(10) DEFAULT '2D'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

CREATE TABLE `pago` (
  `idPago` int(11) NOT NULL,
  `metodo` varchar(50) NOT NULL,
  `estado` varchar(50) NOT NULL,
  `Reserva_idReserva` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

CREATE TABLE `pelicula` (
  `idPelicula` int(11) NOT NULL,
  `titulo` varchar(150) NOT NULL,
  `sinopsis` text DEFAULT NULL,
  `duracion` int(11) DEFAULT NULL,
  `genero` varchar(50) DEFAULT NULL,
  `imagen_url` varchar(255) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

CREATE TABLE `precio_formato` (
  `id_PrecioFormato` int(11) NOT NULL,
  `formato` varchar(10) NOT NULL,
  `precio` decimal(10,2) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

CREATE TABLE `reserva` (
  `idReserva` int(11) NOT NULL,
  `fecha` date NOT NULL,
  `estado` varchar(50) DEFAULT 'pendiente',
  `Usuario_idUsuario` int(11) NOT NULL,
  `Funcion_idFuncion` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

CREATE TABLE `reservaasiento` (
  `idReservaAsiento` int(11) NOT NULL,
  `Reserva_idReserva` int(11) NOT NULL,
  `Asiento_idAsiento` int(11) NOT NULL,
  `precio` decimal(10,2) NOT NULL,
  `estado` varchar(50) DEFAULT 'reservado'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

CREATE TABLE `sala` (
  `idSala` int(11) NOT NULL,
  `numero` int(11) NOT NULL,
  `capacidad` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

CREATE TABLE `ticket` (
  `idTicket` int(11) NOT NULL,
  `codigo` varchar(12) NOT NULL,
  `fecha` date NOT NULL,
  `Reserva_idReserva` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

CREATE TABLE `usuario` (
  `idUsuario` int(11) NOT NULL,
  `nombre` varchar(100) NOT NULL,
  `apellido` varchar(100) NOT NULL,
  `email` varchar(100) NOT NULL,
  `contrasenia` varchar(255) NOT NULL,
  `tipo` enum('Administrador','Cliente') NOT NULL DEFAULT 'Cliente',
  `fecha_registro` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------
-- 3. VOLCADO DE DATOS (Tablas maestras primero)
-- --------------------------------------------------------

INSERT INTO `pelicula` (`idPelicula`, `titulo`, `sinopsis`, `duracion`, `genero`, `imagen_url`) VALUES
(1, 'Avengers: Endgame', 'Los Vengadores se reúnen para deshacer el daño de Thanos.', 181, 'Acción / Ciencia Ficción', 'avengers.jpg'),
(2, 'Interstellar', 'Un grupo de científicos viaja al espacio exterior para salvar a la humanidad.', 169, 'Drama / Sci-Fi', 'interstellar.jpg'),
(3, 'El Padrino', 'La vida de una organización criminal y su transición generacional.', 175, 'Crimen / Drama', 'padrino.jpg'),
(4, 'OBSESIÓN', '', 120, 'Terror', 'https://image.tmdb.org/t/p/w500/rmCkNtzYR2xTOO3ZXmIqB5zgYdE.jpg'),
(5, 'EL DÍA DE LA REVELACIÓN', 'Si descubrieras que no estamos solos...', 120, 'Ciencia ficción', 'https://image.tmdb.org/t/p/w500/pigU63pWFuXkq2MBc865GpFG4UP.jpg'),
(6, 'TOY STORY 5', 'Cuando Woody logra regresar...', 120, 'Animación', 'https://image.tmdb.org/t/p/w500/fWWfKcQDldLgHQwXWakfE16D5vr.jpg'),
(7, 'THE MANDALORIAN AND GROGU', 'Continuación de la serie...', 120, 'Acción', 'https://image.tmdb.org/t/p/w500/sSRaYCfsxgL8LWeBQOO4Syd5BQJ.jpg'),
(8, 'EN LA ZONA GRIS', 'Gira en torno a dos especialistas...', 120, 'Acción', 'https://image.tmdb.org/t/p/w500/yfgquGqeT6DtdsIzPPzTLRABBy0.jpg'),
(9, 'SUPERGIRL', 'Mientras celebra su cumpleaños...', 120, 'Acción', 'https://image.tmdb.org/t/p/w500/diEz9JG1UHEDTN0Yeri5sJZD7PL.jpg'),
(10, 'MINIONS & MONSTRUOS', 'Esta es la historia desenfrenada...', 120, 'Aventura', 'https://image.tmdb.org/t/p/w500/9THY3T4kn5D2rZhwwQ6t7XQtHtv.jpg'),
(11, 'MOANA', 'Moana que quiere ser una viajera...', 120, 'Acción', 'https://image.tmdb.org/t/p/w500/u1dGuYo8OsNlXJVRRRrKeAQxyKk.jpg'),
(12, 'EVIL DEAD: EN LLAMAS', 'Tras la muerte de su esposo...', 120, 'Terror', 'https://image.tmdb.org/t/p/w500/ztadKzIIR0ERYqpHteaPFtk7inP.jpg'),
(13, 'EL AFINADOR', 'Las meticulosas habilidades...', 120, 'Acción', 'https://image.tmdb.org/t/p/w500/xIRryl8bWHFaMDssKFcPAXhfrRB.jpg'),
(14, 'LAS GUERRERAS K-POP', '', 120, 'Fantasía', 'https://image.tmdb.org/t/p/w500/6EQMqEmdG5HoGe2zT1WwWUMvVhv.jpg'),
(15, 'CHICKEN LITTLE', 'Cuando el cielo se está cayendo...', 120, 'Animación', 'https://image.tmdb.org/t/p/w500/AsDUBjrECTVstxCSGvPbwpA0I0M.jpg'),
(16, 'EL CLUB DE LAS PELEADORAS', 'Los impopulares mejores amigos...', 120, 'Comedia', 'https://image.tmdb.org/t/p/w500/zAPPIeqB4cjXiS5qPFgeifndunG.jpg'),
(17, 'LOS PINGÜINOS DE MADAGASCAR', '', 120, 'Acción', 'https://image.tmdb.org/t/p/w500/ynGGKSCUIuZNayNu9lJHFEScx10.jpg'),
(18, 'SPIDER-MAN: UN NUEVO DÍA', '', 120, 'Ciencia ficción', 'https://image.tmdb.org/t/p/w500/riqDLBu3N7UHSi6RFzgtqNC5yws.jpg');

INSERT INTO `sala` (`idSala`, `numero`, `capacidad`) VALUES
(1, 1, 48),
(2, 2, 64),
(3, 3, 32),
(4, 4, 50),
(5, 5, 50),
(6, 6, 40);

INSERT INTO `precio_formato` (`id_PrecioFormato`, `formato`, `precio`) VALUES
(1, '2D', 1000.00),
(2, '3D', 1000.00),
(3, '4D', 1000.00),
(4, 'XD', 1000.00);

INSERT INTO `usuario` (`idUsuario`, `nombre`, `apellido`, `email`, `contrasenia`, `tipo`, `fecha_registro`) VALUES
(1, 'Alan', 'Admin', 'admin@cine.com', 'scrypt:...', 'Administrador', '2026-06-20 17:11:14'),
(2, 'mora', 'sanchez', 'mora@gmail.com', 'scrypt:...', 'Cliente', '2026-06-22 16:49:36'),
(3, 'calle', 'paco', 'calle@gmail.com', 'scrypt:...', 'Cliente', '2026-06-22 16:51:06'),
(4, 'Agustina', 'Miranda', 'agustina@gmail.com', 'scrypt:...', 'Cliente', '2026-06-23 00:14:28'),
(5, 'c', 'p', 'cp@gmail.com', 'scrypt:...', 'Cliente', '2026-06-23 00:28:31');

INSERT INTO `funcion` (`idFuncion`, `titulo`, `genero`, `imagen_url`, `num_sala`, `fecha`, `hora`, `estado`, `idioma`, `Pelicula_idPelicula`, `Sala_idSala`, `formato`) VALUES
(2, 'EL DÍA DE LA REVELACIÓN', 'Ciencia ficción', 'https://image.tmdb.org/t/p/w500/pigU63pWFuXkq2MBc865GpFG4UP.jpg', 2, '2026-06-20', '17:30:00', 'activa', 'Doblada', 5, NULL, '2D'),
(3, 'TOY STORY 5', 'Animación', 'https://image.tmdb.org/t/p/w500/fWWfKcQDldLgHQwXWakfE16D5vr.jpg', 3, '2026-06-20', '18:30:00', 'activa', 'Doblada', 6, NULL, '2D'),
(5, 'EN LA ZONA GRIS', 'Acción', 'https://image.tmdb.org/t/p/w500/yfgquGqeT6DtdsIzPPzTLRABBy0.jpg', 1, '2026-06-20', '20:30:00', 'activa', 'Doblada', 8, NULL, '2D'),
(6, 'SUPERGIRL', 'Acción', 'https://image.tmdb.org/t/p/w500/diEz9JG1UHEDTN0Yeri5sJZD7PL.jpg', 1, '2026-06-25', '16:30:00', 'proximamente', 'Doblada', 9, NULL, '2D'),
(7, 'MINIONS & MONSTRUOS', 'Aventura', 'https://image.tmdb.org/t/p/w500/9THY3T4kn5D2rZhwwQ6t7XQtHtv.jpg', 2, '2026-07-02', '17:30:00', 'activa', 'Doblada', 10, NULL, '2D'),
(8, 'MOANA', 'Acción', 'https://image.tmdb.org/t/p/w500/u1dGuYo8OsNlXJVRRRrKeAQxyKk.jpg', 3, '2026-07-09', '18:30:00', 'proximamente', 'Doblada', 11, NULL, '2D'),
(10, 'EL AFINADOR', 'Acción', 'https://image.tmdb.org/t/p/w500/xIRryl8bWHFaMDssKFcPAXhfrRB.jpg', 2, '2026-06-25', '20:30:00', 'proximamente', 'Doblada', 13, NULL, '2D'),
(21, 'LAS GUERRERAS K-POP', 'Fantasía', 'https://image.tmdb.org/t/p/w500/6EQMqEmdG5HoGe2zT1WwWUMvVhv.jpg', 1, '2026-06-30', '23:23:00', 'activa', 'Subtitulada', 14, NULL, '2D'),
(24, 'LOS PINGÜINOS DE MADAGASCAR', 'Acción', 'https://image.tmdb.org/t/p/w500/ynGGKSCUIN_M', 3, '2026-06-29', '22:00:00', 'activa', 'Doblada', 17, NULL, '2D'),
(25, 'LOS PINGÜINOS DE MADAGASCAR', 'Acción', 'https://image.tmdb.org/t/p/w500/ynGGKSCUIuZNayNu9lJHFEScx10.jpg', 3, '2026-06-29', '20:00:00', 'activa', 'Doblada', 17, NULL, '4D'),
(31, 'OBSESIÓN', 'Terror', 'https://image.tmdb.org/t/p/w500/rmCkNtzYR2xTOO3ZXmIqB5zgYdE.jpg', 1, '2026-06-20', '16:30:00', 'activa', 'Doblada', 4, NULL, '2D'),
(32, 'OBSESIÓN', 'Terror', 'https://image.tmdb.org/t/p/w500/rmCkNtzYR2xTOO3ZXmIqB5zgYdE.jpg', 1, '2026-06-27', '23:58:00', 'activa', 'Doblada', 4, NULL, '3D'),
(33, 'SPIDER-MAN: UN NUEVO DÍA', 'Ciencia ficción', 'https://image.tmdb.org/t/p/w500/riqDLBu3N7UHSi6RFzgtqNC5yws.jpg', 4, '2026-07-03', '00:25:00', 'proximamente', 'Subtitulada', 18, NULL, '2D');

-- --------------------------------------------------------
-- 4. LLAVES PRIMARIAS E ÍNDICES
-- --------------------------------------------------------

ALTER TABLE `asiento`
  ADD PRIMARY KEY (`idAsiento`),
  ADD KEY `Sala_idSala` (`Sala_idSala`);

ALTER TABLE `funcion`
  ADD PRIMARY KEY (`idFuncion`),
  ADD KEY `Pelicula_idPelicula` (`Pelicula_idPelicula`),
  ADD KEY `Sala_idSala` (`Sala_idSala`),
  ADD KEY `fk_funcion_precio_formato` (`formato`);

ALTER TABLE `pago`
  ADD PRIMARY KEY (`idPago`),
  ADD KEY `Reserva_idReserva` (`Reserva_idReserva`);

ALTER TABLE `pelicula`
  ADD PRIMARY KEY (`idPelicula`);

ALTER TABLE `precio_formato`
  ADD PRIMARY KEY (`id_PrecioFormato`),
  ADD UNIQUE KEY `formato` (`formato`);

ALTER TABLE `reserva`
  ADD PRIMARY KEY (`idReserva`),
  ADD KEY `Usuario_idUsuario` (`Usuario_idUsuario`),
  ADD KEY `Funcion_idFuncion` (`Funcion_idFuncion`);

ALTER TABLE `reservaasiento`
  ADD PRIMARY KEY (`idReservaAsiento`),
  ADD KEY `Reserva_idReserva` (`Reserva_idReserva`),
  ADD KEY `Asiento_idAsiento` (`Asiento_idAsiento`);

ALTER TABLE `sala`
  ADD PRIMARY KEY (`idSala`);

ALTER TABLE `ticket`
  ADD PRIMARY KEY (`idTicket`),
  ADD UNIQUE KEY `codigo` (`codigo`),
  ADD KEY `Reserva_idReserva` (`Reserva_idReserva`);

ALTER TABLE `usuario`
  ADD PRIMARY KEY (`idUsuario`),
  ADD UNIQUE KEY `email` (`email`);

-- --------------------------------------------------------
-- 5. AUTO_INCREMENTS
-- --------------------------------------------------------

ALTER TABLE `asiento` MODIFY `idAsiento` int(11) NOT NULL AUTO_INCREMENT;
ALTER TABLE `funcion` MODIFY `idFuncion` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=34;
ALTER TABLE `pago` MODIFY `idPago` int(11) NOT NULL AUTO_INCREMENT;
ALTER TABLE `pelicula` MODIFY `idPelicula` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=19;
ALTER TABLE `precio_formato` MODIFY `id_PrecioFormato` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=5;
ALTER TABLE `reserva` MODIFY `idReserva` int(11) NOT NULL AUTO_INCREMENT;
ALTER TABLE `reservaasiento` MODIFY `idReservaAsiento` int(11) NOT NULL AUTO_INCREMENT;
ALTER TABLE `sala` MODIFY `idSala` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=7;
ALTER TABLE `ticket` MODIFY `idTicket` int(11) NOT NULL AUTO_INCREMENT;
ALTER TABLE `usuario` MODIFY `idUsuario` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=6;

-- --------------------------------------------------------
-- 6. RESTRICCIONES / FOREIGN KEYS
-- --------------------------------------------------------

ALTER TABLE `asiento`
  ADD CONSTRAINT `asiento_ibfk_1` FOREIGN KEY (`Sala_idSala`) REFERENCES `sala` (`idSala`) ON DELETE CASCADE;

ALTER TABLE `funcion`
  ADD CONSTRAINT `fk_funcion_precio_formato` FOREIGN KEY (`formato`) REFERENCES `precio_formato` (`formato`) ON UPDATE CASCADE,
  ADD CONSTRAINT `funcion_ibfk_1` FOREIGN KEY (`Pelicula_idPelicula`) REFERENCES `pelicula` (`idPelicula`),
  ADD CONSTRAINT `funcion_ibfk_2` FOREIGN KEY (`Sala_idSala`) REFERENCES `sala` (`idSala`);

ALTER TABLE `pago`
  ADD CONSTRAINT `pago_ibfk_1` FOREIGN KEY (`Reserva_idReserva`) REFERENCES `reserva` (`idReserva`);

ALTER TABLE `reserva`
  ADD CONSTRAINT `reserva_ibfk_1` FOREIGN KEY (`Usuario_idUsuario`) REFERENCES `usuario` (`idUsuario`),
  ADD CONSTRAINT `reserva_ibfk_2` FOREIGN KEY (`Funcion_idFuncion`) REFERENCES `funcion` (`idFuncion`);

ALTER TABLE `reservaasiento`
  ADD CONSTRAINT `reservaasiento_ibfk_1` FOREIGN KEY (`Reserva_idReserva`) REFERENCES `reserva` (`idReserva`),
  ADD CONSTRAINT `reservaasiento_ibfk_2` FOREIGN KEY (`Asiento_idAsiento`) REFERENCES `asiento` (`idAsiento`);

ALTER TABLE `ticket`
  ADD CONSTRAINT `ticket_ibfk_1` FOREIGN KEY (`Reserva_idReserva`) REFERENCES `reserva` (`idReserva`);

COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;