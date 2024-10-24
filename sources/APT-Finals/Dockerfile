FROM cache.ecsc2024.it/library/golang:1.23-alpine AS builder

RUN apk update && \
    apk add --no-cache git ca-certificates tzdata && \
    update-ca-certificates

WORKDIR /go/src
COPY . .
RUN go build -v -o server ./cmd/server

FROM scratch

COPY --from=builder /usr/share/zoneinfo /usr/share/zoneinfo
COPY --from=builder /etc/ssl/certs/ca-certificates.crt /etc/ssl/certs/
COPY --from=builder /go/src/server /

ENTRYPOINT ["/server"]
