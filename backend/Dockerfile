FROM public.ecr.aws/lambda/python:3.11

COPY package/ ${LAMBDA_TASK_ROOT}

COPY *.py ${LAMBDA_TASK_ROOT}

CMD [ "lambda_function.lambda_handler" ]