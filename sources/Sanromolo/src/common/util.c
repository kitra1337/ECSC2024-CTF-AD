#include <stddef.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/random.h>
#include <sys/types.h>
#include <unistd.h>

#include "common/util.h"

ssize_t read_exactly(int fd, void *buf, size_t size) {
    uint8_t *p = buf;
    ssize_t nread = 0;

    while (size) {
        ssize_t n = read(fd, p + nread, size - nread);
        if (n == 0)
            break;
        if (n < 0)
            return n;

        nread += n;
        size -= n;
    }

    return nread;
}

ssize_t write_exactly(int fd, const void *buf, size_t size) {
    const uint8_t *p = buf;
    ssize_t nwritten = 0;

    while (size) {
        ssize_t n = write(fd, p + nwritten, size - nwritten);
        if (n < 0)
            return n;

        nwritten += n;
        size -= n;
    }

    return nwritten;
}

ssize_t get_rand_bytes(void *buf, size_t size) {
    return getrandom(buf, size, GRND_NONBLOCK);
}

void hex_to_bytes(const char *in_hex, uint8_t *out_bytes, size_t out_size) {
    for (size_t count = 0; count < out_size; count++) {
        sscanf(in_hex, "%02hhx", out_bytes + count);
        in_hex += 2;
    }
}

void bytes_to_hex(char *out_hex, const uint8_t *in_bytes, size_t in_size) {
    for (size_t i = 0; i < in_size; i++) {
        sprintf(out_hex, "%02hhx", in_bytes[i]);
        out_hex += 2;
    }
}

void iso14443a_crc(const uint8_t *data, size_t size, uint8_t *out_crc) {
    uint32_t crc = 0x6363;

    do {
        uint8_t bt;
        bt = *data++;
        bt = (bt ^ (uint8_t)(crc & 0x00FF));
        bt = (bt ^ (bt << 4));
        crc = (crc >> 8) ^ ((uint32_t)bt << 8) ^ ((uint32_t)bt << 3) ^
               ((uint32_t)bt >> 4);
    } while (--size);

    *out_crc++ = (uint8_t)(crc & 0xFF);
    *out_crc = (uint8_t)((crc >> 8) & 0xFF);
}

void flush_stdin(void) {
    int c;

    if (feof(stdin)) {
        fprintf(stderr, "Unexpected end of input");
        exit(1);
    }

    do {
        c = getchar();
        if (c == EOF) {
            fprintf(stderr, "Unexpected end of input");
            exit(1);
        }
    } while (c != '\n');
}

void get_string(char *out, size_t size) {
    if (!fgets(out, size, stdin)) {
        fprintf(stderr, "Unexpected end of input");
        exit(1);
    }

    char *nl = strchr(out, '\n');
    if (nl)
        *nl = '\0';
    else
        flush_stdin();
}

int get_uint(unsigned *value) {
    int res = scanf("%u", value);
    flush_stdin();

    if (res != 1) {
        if (feof(stdin)) {
            fprintf(stderr, "Unexpected end of input");
            exit(1);
        }

        return -1;
    }

    return 0;
}
