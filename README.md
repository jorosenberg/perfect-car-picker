# **🚗 [Perfect Car Picker](https://perfectcarpicker.jonahrosenberg.work/) (https://perfectcarpicker.jonahrosenberg.work/)**

**Perfect Car Picker** is a full-stack, AI-powered vehicle recommendation and financial modeling dashboard. It goes beyond standard car search tools by utilizing Machine Learning to calculate the **True Cost of Ownership (TCO)**—factoring in depreciation, hyper-local energy prices, driving habits, and financing methods—while leveraging Generative AI to provide personalized sales pitches.

## **✨ Core Features**

* 🧠 **ML-Powered Recommendations**: Uses an automated NearestNeighbors algorithm to map user lifestyle inputs (commute distance, family size, "fun factor", luxury preference) to the perfect vehicle match.  
* 💰 **Comprehensive Financial Modeler**: Calculates hyper-accurate monthly cash flow and True Cost of Ownership comparing Cash, Finance, and Lease strategies side-by-side.  
* 🤖 **Generative AI Sales Advisor**: Integrates with **AWS Bedrock** to read vehicle review data and instantly generate personalized, contextual sales pitches based on the user's highest priorities.  
* 🔍 **Strict Multi-Filtering**: Advanced alias-mapping engine to filter complex automotive features (e.g., matching "Autopilot" or "BlueCruise" when a user requests "Hands-Free Driving").

## **🏗️ Cloud Architecture & Infrastructure**

This project was built from the ground up using **Terraform (Infrastructure as Code)** to deploy a highly available, cost-optimized Hybrid Cloud architecture on AWS.

### **Infrastructure Highlights:**

* **Frontend (Thin Client)**: A Streamlit UI containerized with Docker, deployed on an **Amazon EC2** instance (t3.micro). Secured via a Let's Encrypt SSL certificate and an Nginx reverse proxy.  
* **Serverless Backend (Heavy Compute)**: An **AWS Lambda** function serving as the core ML inference and calculation engine. Exposed securely via **Amazon API Gateway**.  
* **Containerized Serverless**: To bypass Lambda's standard 250MB deployment limit (required for heavy data science libraries like pandas and scikit-learn), the backend is packaged as a Docker image and stored in **Amazon ECR**.  
* **Database**: **Amazon RDS (PostgreSQL)** stores the vehicle data, equipped with security groups and automated CI/CD seeding scripts.  
* **Security & IAM**: Database credentials are automatically rotated and retrieved securely at runtime via **AWS Secrets Manager**. Granular IAM Roles enforce the Principle of Least Privilege between EC2, Lambda, and Bedrock.

## **🚀 CI/CD & DevOps Pipeline**

The application features a fully automated GitOps deployment lifecycle powered by **GitHub Actions**:

1. **Infrastructure Provisioning**: Pushing to the main branch triggers Terraform to plan and apply infrastructure updates.  
2. **Image Build & Push**: The backend Docker image is built and pushed to Amazon ECR.  
3. **Zero-Downtime Updates**: The AWS Lambda function is forced to pull the latest image tag upon successful push.  
4. **Automated Database Seeding**: A dedicated workflow opens an SSH tunnel through the EC2 Bastion host to securely execute init\_db.py and migrate the latest vehicle data and ML models into the private RDS instance.

## **📂 Repository Structure**

perfect-car-picker/  
│  
├── .github/workflows/            
│   ├── deploy.yml              \# CI/CD: Terraform Apply & ECR Push  
│   └── seed\_db.yml             \# CI/CD: Secure RDS Database Seeding  
│  
├── app/                        \# 💻 Frontend Application (EC2)  
│   ├── Dockerfile              \# Streamlit container configuration  
│   ├── app.py                  \# Main UI entry point  
│   └── logic.py                \# API Client (Thin architecture)  
│  
├── backend/                    \# ⚡ Serverless Backend (Lambda)  
│   ├── Dockerfile              \# Amazon Linux Lambda container  
│   ├── lambda\_function.py      \# Request handler & routing  
│   ├── car\_recommender.py      \# NearestNeighbors logic  
│   ├── cost\_calculator.py      \# Financial & TCO logic  
│   └── ai\_advisor.py           \# AWS Bedrock GenAI integration  
│  
├── infra/                      \# ☁️ Terraform IaC  
│   ├── main.tf                 \# VPC, EC2, RDS, Lambda, API Gateway  
│   ├── variables.tf            \# Variables & Port configurations  
│   └── user\_data.sh.tpl        \# EC2 bootstrap & Docker launch script  
│  
└── data/                       \# 📊 Data & Database Utils  
    └── init\_db.py              \# PostgreSQL schema & data injection

## **💡 Notes for Hiring Managers**

This project was intentionally designed to demonstrate a broad spectrum of production-ready software engineering skills:

* **System Design & Decoupling**: Initially built as a monolith, the architecture was refactored into a "Thin Client / Heavy Backend" pattern. By moving the Pandas/Scikit-learn processing to AWS Lambda, the EC2 frontend remains incredibly fast and responsive, preventing UI freezes during complex ML calculations.  
* **Cost Optimization**: Designed to operate cleanly within the AWS Free Tier, proving an understanding of cloud cost economics (e.g., choosing containerized Lambda over expensive Fargate clusters for sporadic ML inference).  
* **Infrastructure as Code (IaC)**: Total environment reproducibility via Terraform, meaning the entire AWS stack can be spun up or destroyed with a single command.

## **🛠️ Local Setup & Deployment**

To deploy this infrastructure to your own AWS account:

1. **Clone & Configure**:  
   git clone \[https://github.com/jorosenberg/perfect-car-picker.git\](https://github.com/jorosenberg/perfect-car-picker.git)  
   cd perfect-car-picker/infra

2. **Terraform Init**:  
   terraform init

3. **Provide Variables**: Create a terraform.tfvars file or supply your GitHub Repo URL, Database Username, and Database Password.  
4. **Deploy**:  
   terraform apply

   *Terraform will output the API Gateway URL and the EC2 Public IP upon completion.*