FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir gdown

COPY app/ ./app/
COPY engine/ ./engine/

CMD ["python", "-c", "import os,sys,subprocess; db='/app/data/master_v2.db'; os.makedirs('/app/data',exist_ok=True); (subprocess.run([sys.executable,'-m','gdown','1zFmmt-uNLQWUgtXSPePchqNTp4hXBJoq','-O',db]) if not os.path.exists(db) or os.path.getsize(db)<1000000 else None); os.execv(sys.executable,[sys.executable,'-m','uvicorn','app.main:app','--host','0.0.0.0','--port',os.environ.get('PORT','8000')])"]