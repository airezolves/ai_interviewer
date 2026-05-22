FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY shared/ ./shared/
COPY backend/resume/ ./backend/resume/

EXPOSE 8002
CMD ["uvicorn", "backend.resume.app.main:app", "--host", "0.0.0.0", "--port", "8002"]
