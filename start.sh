#!/bin/sh
# Download master_v2.db from Google Drive if not present in volume
DB_PATH="/app/engine/master_v2.db"
if [ ! -f "$DB_PATH" ] || [ ! -s "$DB_PATH" ]; then
    echo "Downloading master_v2.db from Google Drive..."
    curl -L "https://drive.google.com/uc?export=download&id=1zFmmt-uNLQWUgtXSPePchqNTp4hXBJoq" -o "$DB_PATH"
    echo "Download complete. Size: $(du -sh $DB_PATH)"
else
    echo "master_v2.db already present ($(du -sh $DB_PATH))"
fi
# Start the API
exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
