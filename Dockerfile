FROM python:3.10-slim
WORKDIR /app

# Copy the pyproject.toml first to leverage Docker cache
COPY pyproject.toml .
# We need README.md and auto-sre directory if setuptools tries to install the project
COPY README.md .
COPY auto-sre/ auto-sre/
RUN pip install --no-cache-dir .

# Copy everything else (including inference.py and openenv.yaml at root)
COPY . .

# HF Spaces requires port 7860; PORT env var overrides this
EXPOSE 7860

# Start the Auto-SRE server
CMD ["python", "auto-sre/app.py"]
