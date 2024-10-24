FROM cache.ecsc2024.it/library/python@sha256:feca56bb45e0dfbac0c889aaf6bae9f2484795ce1027698bee08e29157ad91d1

RUN apt install wget

WORKDIR /app
COPY ./requirements.txt requirements.txt
RUN pip install -r requirements.txt

COPY app.py db.py handlers.py validation.py parameters.py music.json ./
COPY init.sh init.sh

ENTRYPOINT [ "/bin/sh", "init.sh"]