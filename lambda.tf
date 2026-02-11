resource "aws_lambda_function" "backend_logic" {
  function_name = "${var.project_name}-logic"
  role          = aws_iam_role.iam_for_lambda.arn
  package_type  = "Image"
  image_uri     = "${aws_ecr_repository.lambda_repo.repository_url}:latest"
  timeout       = 30
  memory_size   = 512
}