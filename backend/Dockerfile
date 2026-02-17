FROM public.ecr.aws/lambda/python:3.11

# 10gb
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY *.py .

CMD [ "lambda_function.lambda_handler" ]