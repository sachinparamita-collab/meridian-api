FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/
COPY engine/ ./engine/

CMD ["python", "-c", "import os,sys,urllib.request; db='/app/data/master_v2.db'; os.makedirs('/app/data',exist_ok=True); (urllib.request.urlretrieve('https://github.com/sachinparamita-collab/meridian-api/releases/download/v0.1.0-data/master_v2.db',db) if not os.path.exists(db) or os.path.getsize(db)<1000000 else None); os.execv(sys.executable,[sys.executable,'-m','uvicorn','app.main:app','--host','0.0.0.0','--port',os.environ.get('PORT','8000')])"]