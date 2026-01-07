# Stage 1: Builder
# Use an official Python runtime as a parent image for the build stage.
# python:3.9-slim-buster provides a minimal Debian-based image with Python 3.9.
FROM python:3.9-slim-buster AS builder

# Set the working directory in the container for the builder stage.
WORKDIR /app

# Install system dependencies required for building Python packages.
# These include development headers for PostgreSQL (libpq-dev) and image processing (libjpeg-dev, zlib1g-dev)
# which are often needed by packages like psycopg2 and Pillow.
# build-essential and gcc are necessary for compiling C extensions.
# The `rm -rf /var/lib/apt/lists/*` command cleans up the APT cache to reduce image size.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
        gcc \
        libjpeg-dev \
        zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy the requirements file into the container.
# This step is done early to leverage Docker's build cache.
COPY requirements.txt .

# Install any needed Python packages specified in requirements.txt.
# --no-cache-dir prevents pip from storing downloaded packages, further reducing image size.
RUN pip install --no-cache-dir -r requirements.txt

# Stage 2: Production Runtime
# Use the same base image for the final production image.
FROM python:3.9-slim-buster

# Set the working directory in the container for the runtime stage.
WORKDIR /app

# Set environment variables for the Flask application and Gunicorn.
# PYTHONUNBUFFERED=1 ensures that Python's stdout and stderr are not buffered,
# which is important for real-time logging in containerized environments.
# FLASK_APP specifies the main Flask application file.
# FLASK_ENV=production sets Flask to production mode, disabling debug features.
# GUNICORN_WORKERS sets the default number of Gunicorn worker processes, which can be overridden.
ENV PYTHONUNBUFFERED 1
ENV FLASK_APP=app.py
ENV FLASK_ENV=production
ENV GUNICORN_WORKERS=4

# Copy only the installed Python packages from the builder stage.
# This significantly reduces the final image size by not including build dependencies.
COPY --from=builder /usr/local/lib/python3.9/site-packages /usr/local/lib/python3.9/site-packages

# Copy the rest of the application code into the container.
# It's recommended to have a .dockerignore file to exclude unnecessary files (e.g., .git, venv).
COPY . .

# Create a non-root user and group for security best practices.
# Running applications as non-root users mitigates potential security vulnerabilities.
# `addgroup --system` and `adduser --system` create system-level group and user.
# `chown -R appuser:appgroup /app` ensures the non-root user owns the application directory.
RUN addgroup --system appgroup && adduser --system --ingroup appgroup appuser \
    && chown -R appuser:appgroup /app

# Switch to the non-root user. All subsequent commands will run as this user.
USER appuser

# Expose the port that Gunicorn will listen on.
# This informs Docker that the container listens on the specified network ports at runtime.
EXPOSE 5000

# Define the command to run the application using Gunicorn.
# Gunicorn is a production-ready WSGI HTTP server for Python web applications.
# -w ${GUNICORN_WORKERS}: Specifies the number of worker processes (default 4, configurable via ENV).
# -b 0.0.0.0:5000: Binds Gunicorn to all network interfaces on port 5000.
# app:app: Refers to the Flask application instance named 'app' within the 'app.py' module.
CMD ["gunicorn", "-w", "${GUNICORN_WORKERS}", "-b", "0.0.0.0:5000", "app:app"]