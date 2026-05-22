FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY shared/ ./shared/
COPY backend/kit_orchestrator/ ./backend/kit_orchestrator/

EXPOSE 8004
CMD ["uvicorn", "backend.kit_orchestrator.app.main:app", "--host", "0.0.0.0", "--port", "8004"]
