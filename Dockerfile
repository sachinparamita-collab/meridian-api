FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/
COPY engine/ ./engine/

CMD ["python", "-c", "import os,urllib.request,subprocess,sys; db='/app/data/master_v2.db'; os.makedirs('/app/data',exist_ok=True); (not os.path.getsize(db) if os.path.exists(db) else True) and urllib.request.urlretrieve('https://drive.google.com/uc?export=download&id=1zFmmt-uNLQWUgtXSPePchqNTp4hXBJoq',db); os.execv(sys.executable,[sys.executable,'-m','uvicorn','app.main:app','--host','0.0.0.0','--port',os.environ.get('PORT','8000')])"]