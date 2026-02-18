#!/bin/bash
set -ex

exec > >(tee /var/log/user-data.log|logger -t user-data -s 2>/dev/console) 2>&1

echo "------------------------------------------------"
echo "Starting Perfect Car Picker User Data Script"
echo "------------------------------------------------"

REPO_URL="${github_repo_url}"
APP_DIR="/home/ubuntu/app"

echo "Repo URL: '$REPO_URL'"

if [ -z "$REPO_URL" ]; then
  echo "ERROR: github_repo_url is empty! Check your Terraform variables."
  exit 1
fi

apt-get update -y
apt-get install -y docker.io git

systemctl start docker || true
systemctl enable docker || true
usermod -a -G docker ubuntu

mkdir -p $APP_DIR
chown -R ubuntu:ubuntu $APP_DIR

sudo -u ubuntu -i bash <<EOF
  cd $APP_DIR
  
  echo "Initializing git..."
  git init
  
  echo "Adding remote..."
  git remote add origin "$REPO_URL"
  
  echo "Configuring sparse checkout for 'frontend' directory..."
  git config core.sparseCheckout true
  echo "frontend/" >> .git/info/sparse-checkout
  
  echo "Pulling main branch..."
  # Try 'main', fallback to 'master' if it fails
  git pull origin main || git pull origin master
EOF

echo "Creating .env file..."
cat <<EOT >> $APP_DIR/.env
API_URL=${api_url}
DB_HOST=${db_host}
DB_PASS=${db_pass}
AWS_DEFAULT_REGION=${aws_region}
APP_PORT=${app_port}
EOT

chown ubuntu:ubuntu $APP_DIR/.env

echo "Building Docker image..."
cd $APP_DIR
docker build -t frontend -f frontend/Dockerfile .

echo "Running container..."
docker run -d \
  -p ${app_port}:${app_port} \
  --restart always \
  --env-file .env \
  --name perfect-car-picker-app \
  frontend

echo "User Data Script Completed Successfully!"