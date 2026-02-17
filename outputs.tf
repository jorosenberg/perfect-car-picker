output "website_url" {
  description = "URL to access the Streamlit App"
  value       = "http://${aws_instance.web_server.public_dns}:${var.app_port}"
}

output "api_url" {
  description = "Endpoint for the Lambda Logic"
  value       = "${aws_apigatewayv2_api.lambda_api.api_endpoint}/calculate"
}