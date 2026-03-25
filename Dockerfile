# Use Python 3.11 (fixes your issue)
FROM python:3.11

# Set working directory
WORKDIR /app

# Copy project files
COPY . .

# Install system dependencies
RUN apt-get update && apt-get install -y \
    pandoc \
    ghostscript \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose port
EXPOSE 10000

# Start app
CMD ["gunicorn", "main:app", "--bind", "0.0.0.0:10000"]