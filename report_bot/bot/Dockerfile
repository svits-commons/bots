FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade -r requirements.txt

COPY . .

# RUN aerich init-db
# RUN aerich migrate
# RUN aerich upgrade

CMD ["python", "bot.py"]
