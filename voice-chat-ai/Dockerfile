# Enhanced AI Interviewer Bot Dockerfile
# Use AWS ECR Public mirror to avoid Docker Hub auth/rate limits
FROM public.ecr.aws/docker/library/python:3.11-slim-bullseye

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    portaudio19-dev \
    libsndfile1 \
    ffmpeg \
    espeak-ng \
    libgl1 \
    libglib2.0-0 \
    python3-dev \
    build-essential \
    curl \
    wget \
    git \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements_enhanced.txt .

# Upgrade pip and install Python dependencies
RUN pip install --upgrade pip setuptools wheel \
    && pip install --no-cache-dir --timeout 300 -r requirements_enhanced.txt

# Download NLTK data for TextBlob
RUN python -c "import nltk; nltk.download('punkt'); nltk.download('brown')"

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p outputs interview-outputs models logs

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/api/enhanced/system/health || exit 1

# Default command
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]