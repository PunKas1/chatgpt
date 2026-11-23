ALTER TABLE dbo.Mensajes
ADD id_remitente int not null,
	id_destinatario	int not null,
 contenido	nvarchar(max) not null,
 FOREIGN key (id_remitente) references Usuarios(id_usuario),
 foreign key (id_destinatario) references Usuarios(id_usuario)

USE GANADORES;
GO

DECLARE @id_borrar INT = 2; -- Cambia a 1 si prefieres borrar 'Andres' y quedarte con 'Andrés'

DELETE FROM dbo.Mensajes
WHERE id_usuario = @id_borrar
   OR id_remitente = @id_borrar
   OR id_destinatario = @id_borrar;

DELETE FROM dbo.Usuarios
WHERE id_usuario = @id_borrar;

USE GANADORES;
GO

CREATE TABLE dbo.Grupos (
    id_grupo INT IDENTITY(1,1) PRIMARY KEY,
    nombre_grupo NVARCHAR(100) NOT NULL,
    id_creador INT NOT NULL,
    fecha_creacion DATETIME DEFAULT GETDATE(),
    FOREIGN KEY (id_creador) REFERENCES dbo.Usuarios(id_usuario)
);

CREATE TABLE dbo.GrupoMiembros (
    id_grupo INT NOT NULL,
    id_usuario INT NOT NULL,
    fecha_union DATETIME DEFAULT GETDATE(),
    PRIMARY KEY (id_grupo, id_usuario),
    FOREIGN KEY (id_grupo) REFERENCES dbo.Grupos(id_grupo) ON DELETE CASCADE,
    FOREIGN KEY (id_usuario) REFERENCES dbo.Usuarios(id_usuario)
);

CREATE TABLE dbo.MensajesGrupo (
    id_mensaje INT IDENTITY(1,1) PRIMARY KEY,
    id_grupo INT NOT NULL,
    id_remitente INT NOT NULL,
    contenido NVARCHAR(MAX) NOT NULL,
    fecha_envio DATETIME DEFAULT GETDATE(),
    FOREIGN KEY (id_grupo) REFERENCES dbo.Grupos(id_grupo) ON DELETE CASCADE,
    FOREIGN KEY (id_remitente) REFERENCES dbo.Usuarios(id_usuario)
);
GO

CREATE TABLE Canales (
    id_canal INT IDENTITY(1,1) PRIMARY KEY,
    nombre_canal NVARCHAR(80) NOT NULL UNIQUE,
    descripcion NVARCHAR(200) NULL,
    id_creador INT NOT NULL,
    fecha_creacion DATETIME NOT NULL DEFAULT GETDATE(),
    CONSTRAINT FK_Canales_Usuarios
        FOREIGN KEY (id_creador) REFERENCES Usuarios(id_usuario)
);