FROM public.ecr.aws/lambda/python:3.11

# possible fix for numpy and pandas
RUN dnf update -y && \
    dnf install -y \
    gcc \
    gcc-c++ \
    make \
    cmake \
    unzip \
    libcurl-devel \
    python3-devel \
    postgresql-devel && \
    dnf clean all

RUN pip install --upgrade pip

# 10gb
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY *.py .

COPY resale_model.joblib .

CMD [ "lambda_function.lambda_handler" ]