ALTER TABLE "auditoria_log" ALTER COLUMN "usuario_id" DROP NOT NULL;

CREATE TABLE IF NOT EXISTS "token_recuperacao" (
	"id" SERIAL,
	"usuario_id" INTEGER NOT NULL,
	"token_hash" VARCHAR(64) NOT NULL UNIQUE,
	"expira_em" TIMESTAMP NOT NULL,
	"usado_em" TIMESTAMP,
	"criado_em" TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
	PRIMARY KEY("id"),
	CONSTRAINT "fk_token_usuario" FOREIGN KEY("usuario_id") REFERENCES "usuario"("id")
		ON UPDATE NO ACTION ON DELETE CASCADE
);