# Use a Debian 12 base so Java 17 installs cleanly
FROM python:3.11-slim-bookworm

# Packages for C++ and Java
RUN apt-get update && \
    apt-get install -y --no-install-recommends g++ openjdk-17-jdk-headless tini && \
    rm -rf /var/lib/apt/lists/*

# Avoid .pyc writes & use unbuffered I/O
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# App code lives in /app (we'll keep it root-owned/read-only to the app user)
WORKDIR /app

# Install Python deps first (better layer caching)
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy the code
COPY . /app

# Create a non-root user and a separate writable work area for temp runs
RUN useradd -m -u 10001 appuser \
    && mkdir -p /sandbox \
    && chown -R appuser:appuser /sandbox \
    && chmod -R a-w /app   # <- Make your app code read-only for everyone

# Switch to non-root
USER appuser

# Expose port for Gunicorn
EXPOSE 8000

# tini = proper init to reap zombies
ENTRYPOINT ["/usr/bin/tini", "--"]

# Start with Gunicorn (adjust wsgi path to your project)
CMD ["gunicorn", "sandbox.wsgi:application", "-b", "0.0.0.0:8000", "--workers", "2", "--threads", "2", "--timeout", "30"]
