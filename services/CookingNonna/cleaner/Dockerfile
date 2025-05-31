FROM ubuntu:22.04

COPY cleaner.sh /var/cleaner.sh
RUN chmod +x /var/cleaner.sh
USER nobody

ENTRYPOINT ["/var/cleaner.sh"]
