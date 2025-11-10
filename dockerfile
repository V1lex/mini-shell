FROM python:3.11-slim
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src ./src

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
  CMD python -m src.main --help >/dev/null || exit 1

CMD ["python", "-m", "src.main"]
