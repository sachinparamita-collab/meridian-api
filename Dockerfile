# ── Stage 1: Build React frontend ──────────────────────────────
FROM node:20-slim AS frontend-build
WORKDIR /frontend
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm install
COPY frontend/ ./
RUN npm run build

# ── Stage 2: Python / FastAPI backend ──────────────────────────
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app/ ./app/
COPY engine/ ./engine/
COPY entrypoint.py ./entrypoint.py

# Copy React build output into the container
COPY --from=frontend-build /frontend/dist ./static

CMD ["python", "entrypoint.py"]