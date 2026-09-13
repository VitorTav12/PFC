CREATE TABLE IF NOT EXISTS "usuario" (
	"id" SERIAL,
	"nome" VARCHAR(150) NOT NULL,
	"email" VARCHAR(255) NOT NULL UNIQUE,
	"senha" VARCHAR(255) NOT NULL,
	"nivel_acesso" VARCHAR(20) NOT NULL CHECK ("nivel_acesso" IN ('secretaria', 'diretoria', 'pais')),
	"criado_em" TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
	PRIMARY KEY("id")
);

CREATE TABLE IF NOT EXISTS "responsavel" (
	"id" SERIAL,
	"usuario_id" INTEGER NOT NULL UNIQUE,
	"nome" VARCHAR(150) NOT NULL,
	"email_pessoal" VARCHAR(255) NOT NULL,
	"criado_em" TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
	PRIMARY KEY("id")
);

CREATE TABLE IF NOT EXISTS "aluno" (
	"id" SERIAL,
	"responsavel_id" INTEGER NOT NULL,
	"nome" VARCHAR(150) NOT NULL,
	"turma" VARCHAR(50) NOT NULL,
	"numero_matricula" VARCHAR(50) NOT NULL UNIQUE,
	"criado_em" TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
	PRIMARY KEY("id")
);

CREATE TABLE IF NOT EXISTS "autorizado" (
	"id" SERIAL,
	"responsavel_id" INTEGER NOT NULL,
	"nome" VARCHAR(150) NOT NULL,
	"grau_parental" VARCHAR(50) NOT NULL,
	"foto" TEXT NOT NULL,
	"criado_em" TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
	PRIMARY KEY("id")
);

CREATE TABLE IF NOT EXISTS "movimentacao" (
	"id" SERIAL,
	"aluno_id" INTEGER NOT NULL,
	"data" DATE NOT NULL DEFAULT CURRENT_DATE,
	"horario" TIME NOT NULL DEFAULT CURRENT_TIME,
	"responsavel_retirou_id" INTEGER,
	"autorizado_retirou_id" INTEGER,
	PRIMARY KEY("id"),
	CONSTRAINT "chk_pessoa_que_retirou" CHECK (
		("responsavel_retirou_id" IS NOT NULL AND "autorizado_retirou_id" IS NULL) OR
		("responsavel_retirou_id" IS NULL AND "autorizado_retirou_id" IS NOT NULL)
	)
);

CREATE TABLE IF NOT EXISTS "auditoria_log" (
	"id" SERIAL,
	"usuario_id" INTEGER NOT NULL,
	"acao" VARCHAR(50) NOT NULL,
	"detalhes" TEXT NOT NULL,
	"data_horario" TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
	PRIMARY KEY("id")
);

ALTER TABLE "responsavel" 
	ADD CONSTRAINT "fk_responsavel_usuario" 
	FOREIGN KEY("usuario_id") REFERENCES "usuario"("id") 
	ON UPDATE NO ACTION ON DELETE CASCADE;

ALTER TABLE "aluno" 
	ADD CONSTRAINT "fk_aluno_responsavel" 
	FOREIGN KEY("responsavel_id") REFERENCES "responsavel"("id") 
	ON UPDATE NO ACTION ON DELETE RESTRICT;

ALTER TABLE "autorizado" 
	ADD CONSTRAINT "fk_autorizado_responsavel" 
	FOREIGN KEY("responsavel_id") REFERENCES "responsavel"("id") 
	ON UPDATE NO ACTION ON DELETE CASCADE;

ALTER TABLE "movimentacao" 
	ADD CONSTRAINT "fk_movimentacao_aluno" 
	FOREIGN KEY("aluno_id") REFERENCES "aluno"("id") 
	ON UPDATE NO ACTION ON DELETE RESTRICT;

ALTER TABLE "movimentacao" 
	ADD CONSTRAINT "fk_movimentacao_responsavel" 
	FOREIGN KEY("responsavel_retirou_id") REFERENCES "responsavel"("id") 
	ON UPDATE NO ACTION ON DELETE RESTRICT;

ALTER TABLE "movimentacao" 
	ADD CONSTRAINT "fk_movimentacao_autorizado" 
	FOREIGN KEY("autorizado_retirou_id") REFERENCES "autorizado"("id") 
	ON UPDATE NO ACTION ON DELETE RESTRICT;

ALTER TABLE "auditoria_log" 
	ADD CONSTRAINT "fk_log_usuario" 
	FOREIGN KEY("usuario_id") REFERENCES "usuario"("id") 
	ON UPDATE NO ACTION ON DELETE RESTRICT;