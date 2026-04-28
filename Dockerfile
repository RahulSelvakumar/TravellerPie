# 1. Use an official lightweight Python image
FROM python:3.11-slim

# 2. Set the working directory to root
WORKDIR /code

# 3. Standard Python environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
# This ensures 'app', 'agents', and 'tools' are all discoverable
ENV PYTHONPATH=/code

# 4. Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends gcc && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# 5. Copy and install requirements
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 6. Copy the entire project (including tools/ and agents/)
COPY . .

# 7. Use the PORT environment variable provided by Cloud Run
ENV PORT=8080
EXPOSE 8080

# 8. Optimized Startup Command
# Using 'python -m uvicorn' ensures the root-level packages are found.
# Using ${PORT} ensures we listen where Google Cloud is looking.
# Use 'exec' to ensure signals (like SIGTERM) are handled correctly by uvicorn
CMD exec uvicorn app.main:app --host 0.0.0.0 --port $PORT