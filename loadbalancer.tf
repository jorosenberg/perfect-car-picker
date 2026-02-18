# resource "aws_lb" "app_lb" {
#   name               = "${var.project_name}-alb"
#   internal           = false
#   load_balancer_type = "application"
#   security_groups    = [aws_security_group.lb_sg.id]
#   subnets            = [aws_subnet.public.id, aws_subnet.public_2.id]

#   tags = { Name = "${var.project_name}-alb" }
# }

# resource "aws_lb_target_group" "app_tg" {
#   name     = "${var.project_name}-tg"
#   port     = var.app_port
#   protocol = "HTTP"
#   vpc_id   = aws_vpc.main.id
#   target_type = "instance"

#   health_check {
#     path                = "/healthz" # streamlit
#     port                = var.app_port
#     healthy_threshold   = 3
#     unhealthy_threshold = 3
#     timeout             = 10
#     interval            = 30
#     matcher             = "200"
#   }
# }

# resource "aws_lb_target_group_attachment" "web_attachment" {
#   target_group_arn = aws_lb_target_group.app_tg.arn
#   target_id        = aws_instance.web_server.id
#   port             = var.app_port
# }