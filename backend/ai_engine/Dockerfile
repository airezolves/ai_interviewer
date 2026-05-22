FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY shared/ ./shared/
COPY backend/ai_engine/ ./backend/ai_engine/

EXPOSE 8003
CMD ["uvicorn", "backend.ai_engine.app.main:app", "--host", "0.0.0.0", "--port", "8003"]
