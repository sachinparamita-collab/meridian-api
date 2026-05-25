FROM python:3.11-slim

WORKDIR /app

# Install requirements first (better layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app code
COPY app/ ./app/

# Copy engine -- .py and .csv files only
COPY engine/ ./engine/

COPY start.sh /start.sh
RUN sed -i 's/\r//' /start.sh && chmod +x /start.sh
CMD ["/start.sh"]