# --- Builder stage: install dependencies using Poetry ---
FROM python:3.11-alpine AS builder
LABEL maintainer="joanvasquez"
ENV PYTHONUNBUFFERED=1

# Install tools needed for building dependencies
RUN apk add --no-cache curl gcc musl-dev

# Install Poetry
ENV POETRY_VERSION=1.2.1
RUN curl -sSL https://install.python-poetry.org | python3 - --version "$POETRY_VERSION"
ENV PATH="/root/.local/bin:$PATH"

# Set workdir and copy only the files needed for dependency resolution
WORKDIR /app
COPY pyproject.toml poetry.lock* ./

# Configure Poetry to install into the system environment and install only production dependencies
RUN poetry config virtualenvs.create false && \
    poetry install --no-dev --no-interaction --no-ansi

# --- Final stage: copy app and runtime dependencies only ---
FROM python:3.11-alpine
LABEL maintainer="joanvasquez"
ENV PYTHONUNBUFFERED=1

# Set work directory
WORKDIR /app

# Copy installed packages and app source from the builder stage
COPY --from=builder /app /app
COPY ./app /app

# Expose port and create a non-root user
EXPOSE 8000
RUN adduser -D -H fastapi-user
USER fastapi-user

# Run FastAPI using Uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
