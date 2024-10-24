FROM node:22

WORKDIR /app
COPY . /app
RUN npm ci

RUN chown -R 1000:1000 /app/files
RUN chmod -R 700 /app/prizes
RUN chmod -R 700 /app/questions

CMD node app.mjs