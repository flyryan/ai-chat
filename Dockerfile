# Build frontend
FROM node:18-alpine as frontend-build
WORKDIR /frontend
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ .
RUN npm run build

# Build backend and serve frontend
FROM python:3.9-slim
WORKDIR /app

# Install Python dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY backend/ .

# Create static directory and copy frontend build
RUN mkdir -p static
COPY --from=frontend-build /frontend/build/ static/

# Add static file serving to main.py
RUN echo 'from fastapi.staticfiles import StaticFiles\napp.mount("/", StaticFiles(directory="static", html=True), name="static")' >> main.py

ENV HOST=0.0.0.0
ENV PORT=8000

EXPOSE 8000
CMD ["gunicorn", "main:app", "--config", "gunicorn.conf.py"]