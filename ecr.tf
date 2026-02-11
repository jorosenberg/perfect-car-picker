resource "aws_ecr_repository" "lambda_repo" {
  name = "${var.project_name}-backend"
}