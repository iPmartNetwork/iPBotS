FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js for admin panel build
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Build admin panel
RUN cd /app/admin-panel && npm install && npm run build && \
    mkdir -p /app/static/admin && \
    cp -r /app/admin-panel/dist/* /app/static/admin/ && \
    rm -rf /app/admin-panel/node_modules

# Create directories
RUN mkdir -p /app/backups /app/logs

CMD ["python", "-m", "bot"]
