resource "aws_instance" "web_server" {
  ami                  = "ami-0c7217cdde317cfec" 
  instance_type        = "t3.micro"
  subnet_id            = aws_subnet.public.id
  vpc_security_group_ids = [aws_security_group.web_sg.id]
  iam_instance_profile = aws_iam_instance_profile.ec2_profile.name
  
  user_data = templatefile("${path.module}/userdata/user_data.sh.tpl", {
    github_repo_url = var.github_repo_url
    api_url         = "${aws_apigatewayv2_api.lambda_api.api_endpoint}/calculate"
    db_host         = aws_db_instance.default.address
    db_pass         = var.db_password
    aws_region      = var.aws_region
    app_port        = var.app_port
  })

  tags = {
    Name = "${var.project_name}-web"
  }
}