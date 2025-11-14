FROM python:3.13.5-slim

WORKDIR /front-bot

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY bot.py .

COPY __init__.py .

COPY app/ ./app

CMD ["python", "bot.py"]