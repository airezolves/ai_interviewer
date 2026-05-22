FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY shared/ ./shared/
COPY backend/auth/ ./backend/auth/

EXPOSE 8001
CMD ["uvicorn", "backend.auth.app.main:app", "--host", "0.0.0.0", "--port", "8001"]
