FROM ubuntu:22.04

WORKDIR /srv/hsm

RUN apt-get update && \
    apt-get install -y python3 qemu-system-arm socat && \
    rm -rf /var/lib/apt/lists/*

CMD ["socat", "TCP-LISTEN:1337,reuseaddr,fork", "EXEC:./hsm.py hsm.bin /srv/hsm_data/db.sqlite"]
