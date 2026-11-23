USE GANADORES;
GO

CREATE TABLE Usuarios (
    id_usuario INT IDENTITY(1,1) PRIMARY KEY,
    nombre_usuario NVARCHAR(50) NOT NULL UNIQUE,
    contrasena NVARCHAR(255) NOT NULL,
    fecha_registro DATETIME DEFAULT GETDATE()
);
GO

CREATE TABLE Mensajes (
    id_mensaje INT IDENTITY(1,1) PRIMARY KEY,
    id_usuario INT NOT NULL,
    
    fecha_envio DATETIME DEFAULT GETDATE(),
    FOREIGN KEY (id_usuario) REFERENCES Usuarios(id_usuario)
);
GO

INSERT INTO Usuarios (nombre_usuario, contrasena) 
VALUES (N'Andres', N'12345');

SELECT * FROM Usuarios;