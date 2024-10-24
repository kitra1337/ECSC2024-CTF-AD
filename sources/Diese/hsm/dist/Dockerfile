FROM cybersecnatlab/socaz:ubuntu-noble

WORKDIR /srv/hsm

RUN apt-get update && apt-get install -y python3 qemu-system-arm

CMD ["socaz", "--bind", "1337", "--timeout", "5", "--cmd", "./hsm.py hsm.bin /srv/hsm_data/db.sqlite"]
