CREATE TABLE IF NOT EXISTS "codigo_2fa" (
	"id" SERIAL,
	"usuario_id" INTEGER NOT NULL,
	"codigo_hash" VARCHAR(64) NOT NULL,
	"expira_em" TIMESTAMP NOT NULL,
	"usado_em" TIMESTAMP,
	"tentativas" INTEGER NOT NULL DEFAULT 0,
	"criado_em" TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
	PRIMARY KEY("id"),
	CONSTRAINT "fk_codigo_2fa_usuario" FOREIGN KEY("usuario_id") REFERENCES "usuario"("id")
		ON UPDATE NO ACTION ON DELETE CASCADE
);