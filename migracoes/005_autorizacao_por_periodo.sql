CREATE TABLE IF NOT EXISTS "autorizacao" (
	"id" SERIAL,
	"autorizado_id" INTEGER NOT NULL,
	"aluno_id" INTEGER NOT NULL,
	"data_inicio" DATE NOT NULL,
	"data_fim" DATE NOT NULL,
	"criado_em" TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
	"revogada_em" TIMESTAMP,
	PRIMARY KEY("id"),
	CONSTRAINT "chk_periodo_autorizacao" CHECK ("data_fim" >= "data_inicio"),
	CONSTRAINT "fk_autorizacao_autorizado" FOREIGN KEY("autorizado_id") REFERENCES "autorizado"("id")
		ON UPDATE NO ACTION ON DELETE CASCADE,
	CONSTRAINT "fk_autorizacao_aluno" FOREIGN KEY("aluno_id") REFERENCES "aluno"("id")
		ON UPDATE NO ACTION ON DELETE CASCADE
);