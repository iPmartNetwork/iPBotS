FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application (this layer invalidates on ANY file change)
COPY . .

# Create directories
RUN mkdir -p /app/backups /app/logs

# Run
CMD ["python", "-m", "bot"]

# Run
CMD ["python", "-m", "bot"]
