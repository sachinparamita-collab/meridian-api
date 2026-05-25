FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/
COPY engine/ ./engine/
COPY entrypoint.py ./entrypoint.py

CMD ["python", "entrypoint.py"]