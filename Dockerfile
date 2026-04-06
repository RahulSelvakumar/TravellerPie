# 1. Use an official lightweight Python image
FROM python:3.11-slim

# 2. Set the working directory inside the container
WORKDIR /code

# 3. Prevent Python from writing .pyc files and enable unbuffered logging
# This ensures you see your "🤖 Graph is thinking..." logs in real-time
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# 4. Set the PYTHONPATH so 'app' and 'agents' can find each other
# This is the FIX for your ModuleNotFoundError
ENV PYTHONPATH=/code

# 5. Install system dependencies if needed (rare for pure Python but safe)
RUN apt-get update && apt-get install -y --no-install-recommends gcc && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# 6. Copy and install requirements
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 7. Copy the entire project into the container
COPY . .

# 8. Set the default Port for Cloud Run
ENV PORT=8000
EXPOSE 8000

# Command to run the FastAPI app
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]