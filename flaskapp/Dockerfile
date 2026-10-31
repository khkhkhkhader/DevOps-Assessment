FROM python:3.9-slim
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends gcc default-libmysqlclient-dev pkg-config && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN useradd --create-home --uid 10001 appuser && chown -R appuser:appuser /app
USER appuser
EXPOSE 5002
CMD ["gunicorn", "--bind", "0.0.0.0:5002", "--workers", "2", "app:app"]
