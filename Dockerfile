# ── Stage 1: Build React frontend ─────────────────────────────────────────────
FROM node:20-slim AS frontend-builder

WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# ── Stage 2: Python backend + built frontend ───────────────────────────────────
FROM python:3.11-slim

WORKDIR /app

# Install Python dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY backend/ ./backend/

# Copy ML model (pre-trained — no training at runtime)
COPY ml/model.pkl ./ml/model.pkl

# Copy built frontend into FastAPI static directory
COPY --from=frontend-builder /app/frontend/dist ./backend/static

# Expose port
EXPOSE 8000

# Start server — use --app-dir so bare imports in backend/ resolve correctly
WORKDIR /app
CMD ["uvicorn", "main:app", "--app-dir", "backend", "--host", "0.0.0.0", "--port", "8000"]
