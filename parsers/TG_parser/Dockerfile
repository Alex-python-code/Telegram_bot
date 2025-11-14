FROM python:3.13.5-slim

WORKDIR /back-bot

RUN apt-get update && apt-get install -y build-essential libssl-dev && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY userbot.py .

COPY parser.session .

COPY db_models/ ./db_models

COPY parser_rq/ ./parser_rq

COPY ai/ ./ai

RUN mkdir -p /app/data

VOLUME /app/data

CMD ["python", "userbot.py"]