FROM python:3.11-slim

WORKDIR /frontend

COPY frontend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY frontend/app.py .
COPY frontend/logic.py .

CMD streamlit run app.py --server.port=$APP_PORT --server.address=0.0.0.0