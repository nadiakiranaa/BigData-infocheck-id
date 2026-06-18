# Dockerfile untuk InfoCheck ID - FastAPI Predict API
FROM python:3.12-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy model, dataset index, and project files
COPY model/model/ /app/model/
COPY komdigi_index.pkl .
COPY api/komdigi_similarity.py api/
COPY api/predict_api.py api/

# Expose port
EXPOSE 8000

# Run FastAPI app with Uvicorn
CMD ["uvicorn", "api.predict_api:app", "--host", "0.0.0.0", "--port", "8000"]
