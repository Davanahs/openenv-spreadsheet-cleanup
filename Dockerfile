FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

# Expose port (default for HF Spaces)
EXPOSE 7860

# NOTE: Do NOT hardcode API_BASE_URL, API_KEY, or MODEL_NAME here.
# The Hackathon evaluator injects these at runtime. Hardcoding overrides injection.

# Run FastAPI server
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "7860"]
