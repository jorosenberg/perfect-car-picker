# Hugging Face Space (Docker SDK) - replaces the AWS Lambda container image
# (was: public.ecr.aws/lambda/python:3.11). Same code, same entry point
# (lambda_function.lambda_handler), now served by a FastAPI shim (app_server.py)
# instead of the Lambda runtime.
FROM python:3.11-slim

ENV JOBLIB_TEMP_FOLDER=/tmp
ENV MPLCONFIGDIR=/tmp

# HF Spaces run as a non-root user
RUN useradd -m -u 1000 user
USER user
ENV PATH="/home/user/.local/bin:$PATH"
WORKDIR /app

COPY --chown=user requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

COPY --chown=user *.py ./

EXPOSE 7860
CMD ["uvicorn", "app_server:app", "--host", "0.0.0.0", "--port", "7860"]
