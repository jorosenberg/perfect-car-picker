#!/bin/bash
set -e

# use apt-get instead of yum
apt-get update -y
apt-get install -y docker.io git

systemctl start docker || true
systemctl enable docker || true

usermod -a -G docker ubuntu

mkdir -p /home/ubuntu/app
chown ubuntu:ubuntu /home/ubuntu/app

cd /home/ubuntu/app

# only clone frontend cuz t3.micro
sudo -u ubuntu git clone --filter=blob:none --no-checkout ${github_repo_url} .

sudo -u ubuntu git sparse-checkout init --cone
sudo -u ubuntu git sparse-checkout set frontend
sudo -u ubuntu git checkout

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