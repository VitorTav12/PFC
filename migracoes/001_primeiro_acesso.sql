ALTER TABLE "usuario" ADD COLUMN IF NOT EXISTS "precisa_trocar_senha" BOOLEAN NOT NULL DEFAULT FALSE;

UPDATE "usuario" SET "precisa_trocar_senha" = TRUE WHERE "nivel_acesso" = 'pais';

CREATE TABLE IF NOT EXISTS "aceite_termo" (
	"id" SERIAL,
	"usuario_id" INTEGER NOT NULL,
	"versao" VARCHAR(20) NOT NULL,
	"aceito_em" TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
	PRIMARY KEY("id"),
	CONSTRAINT "fk_aceite_usuario" FOREIGN KEY("usuario_id") REFERENCES "usuario"("id")
		ON UPDATE NO ACTION ON DELETE RESTRICT
);