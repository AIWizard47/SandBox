# Base Python image
FROM python:3.10-slim-bookworm


# Install system dependencies for C++, Java, etc.
RUN apt-get update && \
    apt-get install -y g++ openjdk-17-jdk-headless && \
    rm -rf /var/lib/apt/lists/*


# Set environment variables
ENV PYTHONUNBUFFERED 1

# Set work directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . .

# Expose Django port
EXPOSE 8000

# Run Django
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
