resource "random_id" "secret_suffix" {
  byte_length = 4
}

resource "aws_secretsmanager_secret" "db_password" {
  name        = "${var.project_name}-db-password-${random_id.secret_suffix.hex}"
  description = "Database password for Perfect Car Picker RDS"
}

resource "aws_secretsmanager_secret_version" "db_password_val" {
  secret_id     = aws_secretsmanager_secret.db_password.id
  secret_string = var.db_password
}