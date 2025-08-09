FROM python:3.11-slim

# Speed + smaller image
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py .

# Cloud Run expects the server on PORT
ENV PORT=8080
CMD exec uvicorn main:app --host 0.0.0.0 --port ${PORT}
