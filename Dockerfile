# Progsity Mock Exam & Sandbox Judge Server
FROM python:3.12-slim

# Install system compilers (g++, gcc) and Node.js for sandboxed evaluation
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    nodejs \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy application files
COPY server.py sandbox_guard.py config.json ./
COPY problems/ ./problems/
COPY static/ ./static/

# Cloud platforms assign a dynamic PORT environment variable (defaults to 5500)
ENV PORT=5500
EXPOSE 5500

CMD ["python", "server.py"]
