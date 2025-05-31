FROM python:3.9-slim

RUN apt-get update && apt-get install -y wget && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY ./requirements.txt requirements.txt
RUN pip install -r requirements.txt

COPY app.py db.py handlers.py validation.py parameters.py music.json ./
COPY init.sh init.sh

ENTRYPOINT [ "/bin/sh", "init.sh"]