FROM node:20-slim

WORKDIR /app
COPY . /app
RUN npm ci

RUN mkdir -p /app/prizes && \
    chmod -R 700 /app/prizes && \
    chmod -R 700 /app/questions

CMD node app.mjs