# 1. Use official Python runtime as a parent image
# Using 3.11-slim to keep the image size low while remaining compatible with your stack
FROM python:3.11-slim

# 2. Set environment variables
# PYTHONUNBUFFERED: Ensures logs are streamed directly to Cloud Logging
# PYTHONDONTWRITEBYTECODE: Prevents Python from writing .pyc files
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8080

# 3. Install system dependencies
# - git: CRITICAL for the Scanner Agent to clone user repositories
# - build-essential: Required to compile Tree-sitter language grammars
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 4. Set the working directory in the container
WORKDIR /app

# 5. Copy requirements file first (to leverage Docker caching)
COPY requirements.txt .

# 6. Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 7. Copy the rest of the application code
COPY . .

# 8. Expose the port (Cloud Run defaults to 8080)
EXPOSE 8080

# 9. Run the web service on container startup
# usage of 'exec' ensures uvicorn receives signals (like SIGTERM) correctly
CMD exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT} --workers 1