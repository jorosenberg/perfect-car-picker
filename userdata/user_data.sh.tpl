#!/bin/bash
set -e # Exit immediately if a command exits with a non-zero status

yum update -y
yum install -y docker git
service docker start
usermod -a -G docker ec2-user

# github secret
git clone ${github_repo_url} /home/ec2-user/app
cd /home/ec2-user/app

# pass in secrets to env
cat <<EOT >> .env
API_URL=${api_url}
DB_HOST=${db_host}
DB_PASS=${db_pass}
AWS_DEFAULT_REGION=${aws_region}
EOT

# build frontend with app port var and envs
docker build -t frontend -f app/Dockerfile .
docker run -d \
  -p ${app_port}:${app_port} \
  --restart always \
  --env-file .env \
  --name perfectcarpicker-app \
  frontend