FROM python:3.11-slim

WORKDIR /app

# Install system dependencies including pandas/openpyxl for Excel files
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    libpq-dev \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install pandas and openpyxl for data loading
RUN pip install pandas openpyxl psycopg2-binary

# Copy application code
COPY . .

# Copy startup scripts
COPY startup_with_data.py /app/startup_with_data.py
COPY startup_with_csv_loader.py /app/startup_with_csv_loader.py
RUN chmod +x /app/startup_with_data.py
RUN chmod +x /app/startup_with_csv_loader.py

# Create non-root user (but don't switch yet for startup)
RUN adduser --disabled-password --gecos '' appuser
RUN chown -R appuser:appuser /app

# Expose port
EXPOSE 4000

# Health check
HEALTHCHECK --interval=10s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:4000/health').raise_for_status()" || exit 1

# Run the application with CSV loader startup script
ENV PYTHONUNBUFFERED=1
CMD ["python", "/app/startup_with_csv_loader.py"] 