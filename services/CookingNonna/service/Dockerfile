FROM ubuntu:22.04

RUN apt-get update && \
    apt-get install -y libssl-dev libgmp-dev socat && \
    rm -rf /var/lib/apt/lists/*

CMD ["socat", "TCP-LISTEN:2222,reuseaddr,fork", "EXEC:/chall/main"]
