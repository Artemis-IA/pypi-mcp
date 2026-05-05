FROM python:3.13-slim

WORKDIR /app

# Install uv for fast Python package management
COPY --from=ghcr.io/astral-sh/uv:0.5 /uv /bin/uv

# Copy project files
COPY pyproject.toml README.md LICENSE ./
COPY src/ ./src/

# Install dependencies
RUN uv pip install --system -e .

# Expose port
EXPOSE 8080

# Healthcheck
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/health')" || exit 1

# Run server
CMD ["pypi-mcp", "--http", "--host", "0.0.0.0", "--port", "8080"]
