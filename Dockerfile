FROM python:3.11-alpine
LABEL maintainer="joanvasquez"

# Recommended to keep Python output unbuffered
ENV PYTHONUNBUFFERED=1

# Install system dependencies (curl for Poetry and build tools)
RUN apk add --no-cache curl build-base

# Install Poetry
ENV POETRY_VERSION=1.2.1

RUN curl -sSL https://install.python-poetry.org | python3 - --version $POETRY_VERSION
ENV PATH="/root/.local/bin:$PATH"

# Set working directory
WORKDIR /app

# Copy Poetry configuration files
COPY pyproject.toml poetry.lock* ./

# Build argument to control dev installation
ARG DEV=false

# Configure Poetry to install dependencies into the container’s Python environment
RUN poetry config virtualenvs.create false && \
    if [ "$DEV" = "true" ]; then \
    poetry install --no-interaction --no-ansi; \
    else \
    poetry install --no-dev --no-interaction --no-ansi; \
    fi

# Copy application code
COPY ./app /app

EXPOSE 8000

# Create a non-root user
RUN adduser -D -H fastapi-user
USER fastapi-user

# Use CMD to run FastAPI with Uvicorn on container start.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
