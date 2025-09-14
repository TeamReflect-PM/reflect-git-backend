# Use official Python slim image
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Copy requirements first (for caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY . .

# Expose port (Cloud Run expects $PORT)
EXPOSE 8081

# Start with Gunicorn in production
CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 main:app
