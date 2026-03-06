FROM python:3.11-slim

WORKDIR /app

# Install system dependencies (cached layer)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy ONLY requirements first — this layer is cached unless requirements.txt changes
COPY backend/requirements.txt ./requirements.txt
RUN pip install --cache-dir /root/.cache/pip -r requirements.txt

# Copy backend code (changes here won't re-trigger pip install)
COPY backend/ ./backend/

# Copy frontend code
COPY frontend/ ./frontend/

# Copy env template
COPY .env .env

WORKDIR /app/backend

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
