FROM python:3.13.5-slim

WORKDIR /bot

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY bot.py .

COPY app/ ./app

COPY db_models/ ./db_models

COPY ai/ ./ai

CMD ["python", "bot.py"]