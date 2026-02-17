FROM python:3.11-slim

WORKDIR /app

COPY app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/app.py .
COPY app/logic.py .

CMD streamlit run app.py --server.port=$APP_PORT --server.address=0.0.0.0