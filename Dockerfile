FROM python:3.12-slim

LABEL maintainer="matiasez.gonzalez@gmail.com"
LABEL description="Quantitative finance research lab — Argentine market connectors, portfolio optimizers, ML forecasting"

# System deps for matplotlib and scipy
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc g++ && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python deps first (better layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the source
COPY src/ src/
COPY benchmarks/ benchmarks/
COPY tests/ tests/
COPY pyproject.toml requirements.txt ./
COPY README.md LICENSE ./

# Install the package in editable mode
RUN pip install --no-cache-dir -e .

# Default: run the tests
CMD ["python", "-m", "pytest", "tests/", "-v", "--tb=short"]
