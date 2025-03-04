# Use an official Python runtime as a parent image.
FROM python:3.11-slim

# Prevent .pyc files and enable unbuffered logging.
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DJANGO_ENV=dev

# Set work directory.
WORKDIR /app

# Install system dependencies and Poetry.
RUN apt-get update && apt-get install -y build-essential curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && curl -sSL https://install.python-poetry.org | python3 - --version 1.5.1
ENV PATH="/root/.local/bin:$PATH"

# Copy Poetry configuration files.
COPY pyproject.toml poetry.lock* ./

# Configure Poetry to install packages into the container.
RUN poetry config virtualenvs.create false && poetry install --only main

# Copy the rest of the application.
COPY . .

# Expose port 8000.
EXPOSE 8000

# Run the FastAPI app using uvicorn.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
