FROM python:3.11-slim

# Install C++ & Java
RUN apt-get update && apt-get install -y g++ openjdk-17-jdk && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Expose Django port
EXPOSE 8000

# Start with Gunicorn (production server)
CMD ["gunicorn", "sandbox.wsgi:application", "--bind", "0.0.0.0:8000"]
