#!/bin/bash
set -e

# use apt-get instead of yum
apt-get update -y
apt-get install -y docker.io git

systemctl start docker
systemctl enable Docker

usermod -a -G docker ubuntu

# only clone frontend cuz t3.micro
git clone --filter=blob:none --no-checkout ${github_repo_url} /home/ubuntu/app
cd /home/ubuntu/app
git sparse-checkout init --cone
git sparse-checkout set frontend
git checkout

cat <<EOT >> .env
API_URL=${api_url}
DB_HOST=${db_host}
DB_PASS=${db_pass}
AWS_DEFAULT_REGION=${aws_region}
APP_PORT=${app_port}
EOT

docker build -t frontend -f frontend/Dockerfile .

docker run -d \
  -p ${app_port}:${app_port} \
  --restart always \
  --env-file .env \
  --name perfect-car-picker-app \
  frontend