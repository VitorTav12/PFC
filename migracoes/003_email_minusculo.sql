UPDATE "usuario" SET "email" = LOWER(TRIM("email"));

UPDATE "responsavel" SET "email_pessoal" = LOWER(TRIM("email_pessoal"));

CREATE UNIQUE INDEX IF NOT EXISTS "idx_usuario_email_minusculo" ON "usuario" (LOWER("email"));