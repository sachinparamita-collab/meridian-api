FROM python:3.11-slim

WORKDIR /app

# Install requirements first (better layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app code
COPY app/ ./app/

# Copy engine — .py and .csv files only (.db and .xlsx excluded by .dockerignore)
COPY engine/ ./engine/

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]