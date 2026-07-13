# Render free web service (Docker) - replaces the AWS Lambda container image
# (was: public.ecr.aws/lambda/python:3.11). Same code, same entry point
# (lambda_function.lambda_handler), now served by a FastAPI shim (app_server.py)
# instead of the Lambda runtime.
FROM python:3.11-slim

ENV JOBLIB_TEMP_FOLDER=/tmp
ENV MPLCONFIGDIR=/tmp

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY *.py ./

EXPOSE 7860
CMD uvicorn app_server:app --host 0.0.0.0 --port ${PORT:-7860}
