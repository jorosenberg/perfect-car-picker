resource "aws_iam_role" "iam_for_lambda" {
  name = "${var.project_name}-lambda-role"
  assume_role_policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Action": "sts:AssumeRole",
      "Principal": { "Service": "lambda.amazonaws.com" },
      "Effect": "Allow"
    }
  ]
}
EOF
}

resource "aws_iam_role" "iam_for_ec2" {
  name = "${var.project_name}-ec2-role"
  assume_role_policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Action": "sts:AssumeRole",
      "Principal": { "Service": "ec2.amazonaws.com" },
      "Effect": "Allow"
    }
  ]
}
EOF
}

resource "aws_iam_policy" "bedrock_access" {
  name        = "${var.project_name}-bedrock-policy"
  description = "Allow access to Bedrock models"
  policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel",
        "bedrock:ListFoundationModels"
      ],
      "Resource": "*"
    }
  ]
}
EOF
}

resource "aws_iam_role_policy_attachment" "lambda_bedrock" {
  role       = aws_iam_role.iam_for_lambda.name
  policy_arn = aws_iam_policy.bedrock_access.arn
}

resource "aws_iam_role_policy_attachment" "ec2_bedrock" {
  role       = aws_iam_role.iam_for_ec2.name
  policy_arn = aws_iam_policy.bedrock_access.arn
}

resource "aws_iam_instance_profile" "ec2_profile" {
  name = "${var.project_name}-ec2-profile"
  role = aws_iam_role.iam_for_ec2.name
}

# --- 7. BACKEND (LAMBDA + API GATEWAY) ---
resource "aws_ecr_repository" "lambda_repo" {
  name = "${var.project_name}-backend"
}

resource "aws_lambda_function" "backend_logic" {
  function_name = "${var.project_name}-logic"
  role          = aws_iam_role.iam_for_lambda.arn
  package_type  = "Image"
  image_uri     = "${aws_ecr_repository.lambda_repo.repository_url}:latest"
  timeout       = 30
  memory_size   = 512
}

resource "aws_apigatewayv2_api" "lambda_api" {
  name          = "${var.project_name}-api"
  protocol_type = "HTTP"
}

resource "aws_apigatewayv2_integration" "lambda_integration" {
  api_id           = aws_apigatewayv2_api.lambda_api.id
  integration_type = "AWS_PROXY"
  integration_uri  = aws_lambda_function.backend_logic.invoke_arn
}

resource "aws_apigatewayv2_route" "default_route" {
  api_id    = aws_apigatewayv2_api.lambda_api.id
  route_key = "POST /calculate"
  target    = "integrations/${aws_apigatewayv2_integration.lambda_integration.id}"
}

resource "aws_apigatewayv2_stage" "default" {
  api_id      = aws_apigatewayv2_api.lambda_api.id
  name        = "$default"
  auto_deploy = true
}

resource "aws_lambda_permission" "api_gw" {
  statement_id  = "AllowExecutionFromAPIGateway"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.backend_logic.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.lambda_api.execution_arn}/*/*"
}