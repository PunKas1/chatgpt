ALTER TABLE dbo.Mensajes
ADD id_remitente int not null,
	id_destinatario	int not null,
 contenido	nvarchar(max) not null,
 FOREIGN key (id_remitente) references Usuarios(id_usuario),
 foreign key (id_destinatario) references Usuarios(id_usuario)