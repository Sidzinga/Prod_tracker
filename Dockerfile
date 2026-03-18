FROM python:3.12-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code and static files
COPY src/ ./src/
COPY static/ ./static/

# Create data and exports directories
RUN mkdir -p /app/data /app/exports

# Set environment variable to force unbuffered output
ENV PYTHONUNBUFFERED=1

EXPOSE 9876

CMD ["python", "-m", "src.web"]
