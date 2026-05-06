FROM python:3.13-slim

ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN pip install --no-cache-dir MacroSignage

EXPOSE 8080

CMD ["macrosignage-prod", "--host", "0.0.0.0", "--port", "8080", "--threads", "4"]
